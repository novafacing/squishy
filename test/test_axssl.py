from pysquishy.squishy import Squishy

code = """#include <unistd.h>

                int retone() {
                    return 1;
                }
                
#define getreg(dest, src)  \
    register long long dest __asm__ (#src); \
    __asm__ ("" :"=r"(dest));
int main() {

                getreg(arg3, r10);
                // read(0, (char*)arg3, (int)(arg3+8));
                int a = retone();
                return a;
                
}
"""


def test_axssl_code() -> None:
    """
    Test compiling axssl code
    """
    squishy = Squishy()
    main_func = squishy.compile(code)
    print(main_func)
