sources = [
    'AggressiveInline.cpp',
    'Check.cpp',
    'DeduplicateCalls.cpp',
    'InlineGlobals.cpp'
]

squishy = shared_library(
    'squishy',
    sources,
    include_directories : inc,
    dependencies: llvm_dep,
    install : false
)
