#include "llvm/Analysis/CallGraph.h"
#include "llvm/Analysis/TargetLibraryInfo.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/IPO/AlwaysInliner.h"
#include "llvm/Transforms/IPO/GlobalDCE.h"

#include <queue>
#include <system_error>

using namespace llvm;

namespace {
class AggressiveInline {
private:
    Module &module;
    ModuleAnalysisManager &module_analysis_manager;
    std::unique_ptr<CallGraph> call_graph;

public:
    AggressiveInline(Module &module, ModuleAnalysisManager &module_analysis_manager)
        : module(module), module_analysis_manager(module_analysis_manager),
          call_graph(std::make_unique<CallGraph>(module)) {}

    std::set<Function *> getCalledFunctions(CallGraphNode *node) const {
        std::set<Function *> calledFunctions;
        std::transform(node->begin(), node->end(),
                       std::inserter(calledFunctions, calledFunctions.begin()),
                       [](std::pair<Optional<WeakTrackingVH>, CallGraphNode *> node) {
                           return node.second->getFunction();
                       });

        std::vector<Function *> calledFunctionsVector(calledFunctions.begin(),
                                                      calledFunctions.end());
        while (!calledFunctionsVector.empty()) {
            auto top = calledFunctionsVector.back();
            calledFunctionsVector.pop_back();
            auto topNode = call_graph->getOrInsertFunction(top);

            for (auto it = topNode->begin(); it != topNode->end(); ++it) {
                auto calledFunction = it->second->getFunction();

                if (calledFunctions.find(calledFunction) == calledFunctions.end()) {
                    calledFunctions.insert(calledFunction);
                    calledFunctionsVector.push_back(calledFunction);
                }
            }
        }
        return calledFunctions;
    }

    void inlineFunctions() {
        // Honestly, this isn't necessary, but if more optimization to this process or
        // manual inlining is needed in the future, this will be probably required
        auto callsSortKey = [this](Function *f, Function *g) {
            auto fnode = call_graph->getOrInsertFunction(f);
            auto gnode = call_graph->getOrInsertFunction(g);
            // Return whether the number of calls made by f is greater than g.
            // Maintains order of least calls made is first in the worklist
            return getCalledFunctions(fnode).size() >
                       getCalledFunctions(gnode).size() ||
                   g->getName() != "main"; // Sort main last
        };

        std::priority_queue<Function *, std::vector<Function *>, decltype(callsSortKey)>
            worklist(callsSortKey);
        std::set<Function *> shouldBeRemoved;

        for (auto &f : module) {
            worklist.push(&f);
        }

        // Apply the inliner properties to everything but the most toplevel function
        // (main)
        while (worklist.size() > 1) {
            Function *f = worklist.top();
            errs() << "Checking " << f->getName() << "\n";
            f->print(errs(), nullptr);
            shouldBeRemoved.insert(f);
            worklist.pop();
            // Make the function inlinable
            f->removeFnAttr(Attribute::NoInline);
            f->removeFnAttr(Attribute::OptimizeNone);
            f->addFnAttr(Attribute::AlwaysInline);
        }

        LibFunc library_func;
        // Check whether any function for removal is a library function and error if so
        for (auto f : shouldBeRemoved) {
            auto info = TargetLibraryInfoWrapperPass().getTLI(*f);
            if (info.getLibFunc(f->getName(), library_func)) {
                report_fatal_error(createStringError(std::errc::function_not_supported,
                                                     "Function %s is not available",
                                                     f->getName().str().c_str()),
                                   false);
            }
        }

        // Run the inliner to force inline everything into the main function (this works
        // recursively)
        auto inliner_result =
            AlwaysInlinerPass(false).run(module, module_analysis_manager);

        // Remove newly inlined functions from their parents
        for (auto f : shouldBeRemoved) {
            errs() << "Removing function " << f->getName() << "\n";
            f->replaceAllUsesWith(PoisonValue::get(f->getType()));
            f->eraseFromParent();
        }

        // Remove newly dead code resulting from inlining
        auto dce_result = GlobalDCEPass().run(module, module_analysis_manager);
    }

    /// C may have non-instruction users, and
    /// allNonInstructionUsersCanBeMadeInstructions has returned true. Convert the
    /// non-instruction users to instructions.
    static void makeAllConstantUsesInstructions(Constant *constant) {
        SmallVector<ConstantExpr *, 4> users;

        for (auto *user : constant->users()) {
            if (isa<ConstantExpr>(user)) {
                users.push_back(cast<ConstantExpr>(user));
            } else {
                // We should never get here; allNonInstructionUsersCanBeMadeInstructions
                // should not have returned true for C.
                assert(
                    isa<Instruction>(user) &&
                    "Can't transform non-constantexpr non-instruction to instruction!");
            }
        }

        SmallVector<Value *, 4> user_users;

        for (auto *user : users) {
            user_users.clear();
            append_range(user_users, user->users());

            for (auto *user_user : user_users) {
                Instruction *user_user_instruction = cast<Instruction>(user_user);
                Instruction *new_user = user->getAsInstruction(user_user_instruction);
                user_user_instruction->replaceUsesOfWith(user, new_user);
            }
            // We've replaced all the uses, so destroy the constant. (destroyConstant
            // will update value handles and metadata.)
            user->destroyConstant();
        }
    }

    static Function *getGlobalUser(GlobalVariable *g) {
        Function *rv = nullptr;

        for (auto user : g->users()) {
            Function *fuser = nullptr;

            if (isa<Function>(user)) {
                fuser = cast<Function>(user);
            } else if (isa<Instruction>(user)) {
                // Parent block, parent function
                fuser = cast<Instruction>(user)->getParent()->getParent();
            }

            if (fuser != nullptr && rv != nullptr && fuser != rv) {
                report_fatal_error(
                    createStringError(
                        std::errc::io_error,
                        "Global variable %s must be used by only one function",
                        g->getName().str().c_str()),
                    false);
            }

            rv = fuser;
        }

        return rv;
    }

    static void disaggregateVars(Instruction *after_instr, Value *val,
                                 SmallVectorImpl<Value *> &val_idx,
                                 ConstantAggregate &const_aggregate,
                                 SmallSetVector<GlobalVariable *, 4> &vars) {
        SmallSetVector<Value *, 4> vars_to_undef;

        Constant *constant;
        for (unsigned i = 0; (constant = const_aggregate.getAggregateElement(i)); i++) {
            val_idx.push_back(ConstantInt::get(
                Type::getInt32Ty(after_instr->getParent()->getContext()), i));

            if (isa<ConstantAggregate>(constant)) {
                disaggregateVars(after_instr, val, val_idx,
                                 cast<ConstantAggregate>(*constant), vars);

            } else if (isa<ConstantExpr>(constant) ||
                       (isa<GlobalVariable>(constant) &&
                        vars.count(cast<GlobalVariable>(constant)))) {
                GetElementPtrInst *gep_instr =
                    GetElementPtrInst::CreateInBounds(val->getType(), val, val_idx);
                gep_instr->insertAfter(after_instr);

                vars_to_undef.insert(constant);

                new StoreInst(constant, gep_instr, gep_instr->getNextNode());
            }

            val_idx.pop_back();
        }

        for (auto *var_to_undef : vars_to_undef) {
            const_aggregate.handleOperandChange(
                var_to_undef, UndefValue::get(var_to_undef->getType()));
        }
    }

    static void extractValuesFromStore(StoreInst *inst,
                                       SmallSetVector<GlobalVariable *, 4> &vars) {
        Value *store_value = inst->getValueOperand();
        if (!isa<ConstantAggregate>(store_value))
            return;

        SmallVector<Value *, 4> idx;
        idx.push_back(
            ConstantInt::get(Type::getInt32Ty(inst->getParent()->getContext()), 0));

        disaggregateVars(inst, inst->getPointerOperand(), idx,
                         cast<ConstantAggregate>(*store_value), vars);
    }

    void inlineGlobalsIntoFunction(SmallSetVector<GlobalVariable *, 4> &globals,
                                   Function *f) {
        auto &entry_bb = f->getEntryBlock();
        auto entry_insertion = &*entry_bb.getFirstInsertionPt();
        SmallMapVector<GlobalVariable *, Instruction *, 4> global_to_instruction;
        Instruction *insertion_point = entry_insertion;

        for (auto g : globals) {
            Instruction *alloc_global_space_instr = new AllocaInst(
                g->getValueType(), g->getType()->getAddressSpace(), nullptr,
                g->getAlign().valueOrOne(), "", insertion_point);

            alloc_global_space_instr->takeName(g);
            global_to_instruction[g] = alloc_global_space_instr;

            if (g->hasInitializer()) {
                Constant *global_init = g->getInitializer();
                StoreInst *store_global_init = new StoreInst(
                    global_init, alloc_global_space_instr, insertion_point);
                g->setInitializer(nullptr);
                extractValuesFromStore(store_global_init, globals);

                insertion_point = store_global_init;
            }
        }

        for (auto p : global_to_instruction) {
            makeAllConstantUsesInstructions(p.first);
            p.first->replaceAllUsesWith(p.second);
            p.first->eraseFromParent();
        }
    }

    // This function is mostly taken from SheLLVM
    void inlineGlobalVars() {
        // Map of functions to global variables that are used in them (there must be
        // only one user of a global variable)
        SmallMapVector<Function *, SmallSetVector<GlobalVariable *, 4>, 4>
            globals_for_functions;

        for (auto &g : module.globals()) {
            Function *f = getGlobalUser(&g);
            if (!f) {
                report_fatal_error(
                    createStringError(std::errc::io_error,
                                      "Global variable %s has no function user",
                                      g.getName().str().c_str()),
                    false);
            }
            globals_for_functions[f].insert(&g);
        }

        for (auto p : globals_for_functions) {
            inlineGlobalsIntoFunction(p.second, p.first);
        }
    }

    void removeUndefCalls() {
        std::set<CallInst *> call_instrs;
        for (auto &f : module) {
            for (auto &bb : f) {
                for (auto &i : bb) {
                    if (auto possible_poison_call = dyn_cast<CallInst>(&i)) {
                        call_instrs.insert(possible_poison_call);
                    }
                }
            }
        }
        for (auto &possible_poison_call : call_instrs) {
            if (isa<PoisonValue>(possible_poison_call->getCalledOperand())) {
                possible_poison_call->eraseFromParent();
            }
        }
    }

    void run() {
        inlineFunctions();
        inlineGlobalVars();
        removeUndefCalls();
        if (verifyModule(module)) {
            module.print(errs(), nullptr);
            report_fatal_error(
                createStringError(
                    std::errc::operation_canceled,
                    "Module is not valid! Something went terribly wrong.\n"
                    "Do not use the inline keyword in your input!\n"),
                false);
        }
    }
};

struct Check : PassInfoMixin<Check> {
    PreservedAnalyses run(Module &module, ModuleAnalysisManager &mam) {
        AggressiveInline ai(module, mam);
        ai.run();
        return PreservedAnalyses::all();
    }
};

struct LegacyCheck : public ModulePass {
    static char ID;
    LegacyCheck() : ModulePass(ID) {}
    bool runOnModule(Module &module) override {
        ModuleAnalysisManager mam;
        AggressiveInline ai(module, mam);
        ai.run();
        return false;
    }
};
} // namespace

llvm::PassPluginLibraryInfo getSquishyInlinePluginInfo() {
    return {LLVM_PLUGIN_API_VERSION, "SquishyInline", LLVM_VERSION_STRING,
            [](PassBuilder &pass_builder) {
                pass_builder.registerPipelineParsingCallback(
                    [](StringRef name, ModulePassManager &module_pass_manager,
                       ArrayRef<PassBuilder::PipelineElement>) {
                        if (name == "squishy-inline") {
                            module_pass_manager.addPass(Check());
                            return true;
                        }
                        return false;
                    });
            }};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo llvmGetPassPluginInfo() {
    return getSquishyInlinePluginInfo();
}

char LegacyCheck::ID = 0;

static RegisterPass<LegacyCheck> X("squishy-inline" /* Pass Arg */,
                                   "Squishy Inline" /* Name */, true /* CFG Only */,
                                   false /* Is analysis */);