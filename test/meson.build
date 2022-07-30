test(
    'Emit bitcode for test check program',
    clang,
    args: [
        '-c',
        '-emit-llvm',
        '-x',
        'c',
        '-o',
        'check.bc',
        'check.c'
    ],
    priority: 2,
    workdir: meson.current_source_dir()
)

test(
    'Emit bitcode for shouldail test check program',
    clang,
    args: [
        '-c',
        '-emit-llvm',
        '-x',
        'c',
        '-o',
        'check_lib_shouldfail.bc',
        'check_lib_shouldfail.c'
    ],
    priority: 2,
    workdir: meson.current_source_dir()
)

test(
    'Emit bitcode for axssl test program',
    clang,
    args: [
        '-c',
        '-emit-llvm',
        '-x',
        'c',
        '-o',
        'axssl_unopt.bc',
        'axssl.c'
    ],
    priority: 2,
    workdir: meson.current_source_dir()
)

test(
    'Test inline program', 
    llvm_opt,
    args: [
        '-load-pass-plugin',
        squishy.full_path(), 
        '-passes=squishy-inline', 
        '-o',
        'check_opt.bc',
        'check.bc'
    ],
    priority: 1,
    workdir: meson.current_source_dir()
)

test(
    'Test shouldfail inline program', 
    llvm_opt,
    args: [
        '-load-pass-plugin',
        squishy.full_path(), 
        '-passes=squishy-inline', 
        '-S',
        'check_lib_shouldfail.bc'
    ],
    priority: 1,
    workdir: meson.current_source_dir(),
    should_fail: true
)

test(
    'Test axssl program', 
    llvm_opt,
    args: [
        '-load-pass-plugin',
        squishy.full_path(), 
        '-passes=squishy-inline', 
        '-o',
        'axssl.bc',
        'axssl_unopt.bc'
    ],
    priority: 1,
    workdir: meson.current_source_dir()
)


test(
    'Test compile inline program',
    clang,
    args: [
        '-Oz',
        '-x',
        'ir',
        '-o',
        'check.bin',
        'check_opt.bc'
    ],
    priority: 0,
    workdir: meson.current_source_dir(),
)

test(
    'Test compile inline program',
    clang,
    args: [
        '-Oz',
        '-x',
        'ir',
        '-o',
        'axssl.bin',
        'axssl.bc'
    ],
    priority: 0,
    workdir: meson.current_source_dir(),
)