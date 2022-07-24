test(
    'Emit bitcode for test check program',
    clang,
    args: [
        '-c',
        '-emit-llvm',
        '-x',
        'c',
        '-o',
        'check.ll',
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
        'check_lib_shouldfail.ll',
        'check_lib_shouldfail.c'
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
        'check_opt.ll',
        'check.ll'
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
        'check_lib_shouldfail.ll'
    ],
    priority: 1,
    workdir: meson.current_source_dir(),
    should_fail: true
)

test(
    'Test compile and run inline program',
    clang,
    args: [
        '-Oz',
        '-x',
        'ir',
        '-o',
        'check',
        'check_opt.ll'
    ],
    priority: 0,
    workdir: meson.current_source_dir(),
)