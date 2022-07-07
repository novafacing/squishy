#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

namespace {
void visitFunction(Function &function) {
    errs() << "Visiting function: " << function.getName() << "\n";
}

struct Check : PassInfoMixin<Check> {
    PreservedAnalyses run(Function &function, FunctionAnalysisManager &fam) {
        visitFunction(function);
        return PreservedAnalyses::all();
    }
};

struct LegacyCheck : public FunctionPass {
    static char ID;
    LegacyCheck() : FunctionPass(ID) {}
    bool runOnFunction(Function &function) override {
        visitFunction(function);
        return false;
    }
};
} // namespace

llvm::PassPluginLibraryInfo getCheckPluginInfo() {
    return {LLVM_PLUGIN_API_VERSION, "Check", LLVM_VERSION_STRING,
            [](PassBuilder &pass_builder) {
                pass_builder.registerPipelineParsingCallback(
                    [](StringRef name, FunctionPassManager &function_pass_manager,
                       ArrayRef<PassBuilder::PipelineElement>) {
                        if (name == "check") {
                            function_pass_manager.addPass(Check());
                            return true;
                        }
                        return false;
                    });
            }};
}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo llvmGetPassPluginInfo() {
    return getCheckPluginInfo();
}

char LegacyCheck::ID = 0;

static RegisterPass<LegacyCheck> X("check" /* Pass Arg */, "Check pass" /* Name */,
                                   true /* CFG Only */, false /* Is analysis */);