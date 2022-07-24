project(
    'squishy',
    ['c', 'cpp'],
    version: '1.0.0',
    license: 'MIT'
)

llvm_dep = dependency('llvm', version : '>=15.0.0')
llvm_opt = find_program(llvm_dep.get_variable(configtool: 'bindir') / 'opt')
clang = find_program('clang')

inc = include_directories('include')

subdir('src')
subdir('test')
