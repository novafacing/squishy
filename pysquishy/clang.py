"""
Clang helper for squishy library
"""

from enum import Enum
from itertools import chain, repeat
from logging import getLogger
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError, run
from tempfile import NamedTemporaryFile
from typing import List, Optional, Tuple, Union

from pysquishy.error import CompilationError

logger = getLogger(__name__)


class ClangArch(str, Enum):
    """
    Architecture options for clang as of LLVM 15.0.0

    The "original list" of these options is
    [here](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Support/Triple.cpp),
    """

    i386 = "i386"
    i486 = "i486"
    i586 = "i586"
    i686 = "i686"
    i786 = "i786"
    i886 = "i886"
    i986 = "i986"
    amd64 = "amd64"
    x86_64 = "x86_64"
    x86_64h = "x86_64h"
    powerpc = "powerpc"
    powerpcspe = "powerpcspe"
    ppc = "ppc"
    ppc32 = "ppc32"
    powerpcle = "powerpcle"
    ppcle = "ppcle"
    ppc32le = "ppc32le"
    powerpc64 = "powerpc64"
    ppu = "ppu"
    ppc64 = "ppc64"
    powerpc64le = "powerpc64le"
    ppc64le = "ppc64le"
    xscale = "xscale"
    xscaleeb = "xscaleeb"
    aarch64 = "aarch64"
    aarch64_be = "aarch64_be"
    aarch64_32 = "aarch64_32"
    arc = "arc"
    arm64 = "arm64"
    arm64_32 = "arm64_32"
    arm64e = "arm64e"
    arm = "arm"
    armeb = "armeb"
    thumb = "thumb"
    thumbeb = "thumbeb"
    avr = "avr"
    m68k = "m68k"
    msp430 = "msp430"
    mips = "mips"
    mipseb = "mipseb"
    mipsallegrex = "mipsallegrex"
    mipsisa32r6 = "mipsisa32r6"
    mipsr6 = "mipsr6"
    mipsel = "mipsel"
    mipsallegrexel = "mipsallegrexel"
    mipsisa32r6el = "mipsisa32r6el"
    mipsr6el = "mipsr6el,"
    mips64 = "mips64"
    mips64eb = "mips64eb"
    mipsn32 = "mipsn32"
    mipsisa64r6 = "mipsisa64r6,"
    mips64r6 = "mips64r6"
    mipsn32r6 = "mipsn32r6"
    mips64el = "mips64el"
    mipsn32el = "mipsn32el"
    mipsisa64r6el = "mipsisa64r6el"
    mips64r6el = "mips64r6el,"
    mipsn32r6el = "mipsn32r6el"
    r600 = "r600"
    amdgcn = "amdgcn"
    riscv32 = "riscv32"
    riscv64 = "riscv64"
    hexagon = "hexagon"
    s390x = "s390x"
    systemz = "systemz"
    sparc = "sparc"
    sparcel = "sparcel"
    sparcv9 = "sparcv9"
    sparc64 = "sparc64"
    tce = "tce"
    tcele = "tcele"
    xcore = "xcore"
    nvptx = "nvptx"
    nvptx64 = "nvptx64"
    le32 = "le32"
    le64 = "le64"
    amdil = "amdil"
    amdil64 = "amdil64"
    hsail = "hsail"
    hsail64 = "hsail64"
    spir = "spir"
    spir64 = "spir64"
    spirv32 = "spirv32"
    spirv32v1_0 = "spirv32v1.0"
    spirv32v1_1 = "spirv32v1.1"
    spirv32v1_2 = "spirv32v1.2,"
    spirv32v1_3 = "spirv32v1.3"
    spirv32v1_4 = "spirv32v1.4"
    spirv32v1_5 = "spirv32v1.5"
    spirv64 = "spirv64"
    spirv64v1_0 = "spirv64v1.0"
    spirv64v1_1 = "spirv64v1.1"
    spirv64v1_2 = "spirv64v1.2,"
    spirv64v1_3 = "spirv64v1.3"
    spirv64v1_4 = "spirv64v1.4"
    spirv64v1_5 = "spirv64v1.5"
    lanai = "lanai"
    renderscript32 = "renderscript32"
    renderscript64 = "renderscript64"
    shave = "shave"
    ve = "ve"
    wasm32 = "wasm32"
    wasm64 = "wasm64"
    csky = "csky"
    loongarch32 = "loongarch32"
    loongarch64 = "loongarch64"
    dxil = "dxil"
    NONE = ""


class ClangVendor(str, Enum):
    """
    Vendor options for clang as of LLVM 15.0.0

    The "original list" of these options is
    [here](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Support/Triple.cpp),
    """

    apple = "apple"
    pc = "pc"
    scei = "scei"
    sie = "sie"
    fsl = "fsl"
    ibm = "ibm"
    img = "img"
    mti = "mti"
    nvidia = "nvidia"
    csr = "csr"
    myriad = "myriad"
    amd = "amd"
    mesa = "mesa"
    suse = "suse"
    oe = "oe"
    NONE = ""


class ClangOS(str, Enum):
    """
    OS options for clang as of LLVM 15.0.0

    The "original list" of these options is
    [here](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Support/Triple.cpp),
    """

    ananas = "ananas"
    cloudabi = "cloudabi"
    darwin = "darwin"
    dragonfly = "dragonfly"
    freebsd = "freebsd"
    fuchsia = "fuchsia"
    ios = "ios"
    kfreebsd = "kfreebsd"
    linux = "linux"
    lv2 = "lv2"
    macos = "macos"
    netbsd = "netbsd"
    openbsd = "openbsd"
    solaris = "solaris"
    win32 = "win32"
    windows = "windows"
    zos = "zos"
    haiku = "haiku"
    minix = "minix"
    rtems = "rtems"
    nacl = "nacl"
    aix = "aix"
    cuda = "cuda"
    nvcl = "nvcl"
    amdhsa = "amdhsa"
    ps4 = "ps4"
    ps5 = "ps5"
    elfiamcu = "elfiamcu"
    tvos = "tvos"
    watchos = "watchos"
    driverkit = "driverkit"
    mesa3d = "mesa3d"
    contiki = "contiki"
    amdpal = "amdpal"
    hermit = "hermit"
    hurd = "hurd"
    wasi = "wasi"
    emscripten = "emscripten"
    shadermodel = "shadermodel"
    NONE = ""


class ClangEnvironment(str, Enum):
    """
    Environment options for clang as of LLVM 15.0.0

    The "original list" of these options is
    [here](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Support/Triple.cpp),
    """

    eabihf = "eabihf"
    eabi = "eabi"
    gnuabin32 = "gnuabin32"
    gnuabi64 = "gnuabi64"
    gnueabihf = "gnueabihf"
    gnueabi = "gnueabi"
    gnux32 = "gnux32"
    gnu_ilp32 = "gnu_ilp32"
    code16 = "code16"
    gnu = "gnu"
    android = "android"
    musleabihf = "musleabihf"
    musleabi = "musleabi"
    muslx32 = "muslx32"
    musl = "musl"
    msvc = "msvc"
    itanium = "itanium"
    cygnus = "cygnus"
    coreclr = "coreclr"
    simulator = "simulator"
    macabi = "macabi"
    pixel = "pixel"
    vertex = "vertex"
    geometry = "geometry"
    hull = "hull"
    domain = "domain"
    compute = "compute"
    library = "library"
    raygeneration = "raygeneration"
    intersection = "intersection"
    anyhit = "anyhit"
    closesthit = "closesthit"
    miss = "miss"
    callable = "callable"
    mesh = "mesh"
    amplification = "amplification"
    NONE = ""


class ClangHelper:
    """
    Helper class for clang
    """

    @classmethod
    def test_command(cls, command: Path) -> None:
        """
        Test a command with a --version option that it can run

        :param command: The command to test
        """
        cmd = [str(command.resolve()), "--version"]
        try:
            run(cmd, capture_output=True, check=True)
        except CalledProcessError as e:
            raise FileNotFoundError(f"{command} not found or not runnable") from e

    def __init__(
        self,
        clang: Union[str, Path] = "clang",
        opt: Union[str, Path] = "opt",
    ):
        """
        Initialize the helper class

        :param clang: The clang command to use if not the default
        :param opt: The opt command to use if not the default
        """

        if isinstance(clang, str):
            clang_path = which(clang)

            if clang_path is None:
                raise FileNotFoundError(f"{clang} not found")

            clang = Path(clang_path)
        else:
            clang = Path(clang)

        if not clang.is_file():
            raise FileNotFoundError(f"{clang} not found")

        if isinstance(opt, str):
            opt_path = which(opt)

            if opt_path is None:
                raise FileNotFoundError(f"{opt} not found")

            opt = Path(opt_path)
        else:
            opt = Path(opt)

        if not opt.is_file():
            raise FileNotFoundError(f"{opt} not found")

        self.clang = clang
        self.opt = opt
        self.test_command(self.clang)
        self.test_command(self.opt)

    def triple(
        self,
    ) -> Tuple[Union[ClangArch, ClangVendor, ClangOS, ClangEnvironment], ...]:
        """
        Get the target triple for the current architecture
        """
        res = run([self.clang, "-print-target-triple"], capture_output=True, check=True)
        triple: List[Union[ClangArch, ClangVendor, ClangOS, ClangEnvironment]] = []

        for elem, triple_component in zip(
            chain(res.stdout.decode("utf-8").strip().split("-"), repeat("")),
            (ClangArch, ClangVendor, ClangOS, ClangEnvironment),
        ):
            triple.append(triple_component(elem))

        return tuple(triple)

    def emit_bitcode(
        self,
        source: Union[str, Path],
        arch: ClangArch = ClangArch.NONE,
        vendor: ClangVendor = ClangVendor.NONE,
        os: ClangOS = ClangOS.NONE,
        environment: ClangEnvironment = ClangEnvironment.NONE,
        extra_args: Optional[List[str]] = None,
    ) -> bytes:
        """
        Emit bitcode from a source file

        :param source: The source file or string to compile to bitcode
        :param arch: The architecture to compile for
        :param vendor: The vendor to compile for
        :param os: The OS to compile for
        :param environment: The environment to compile for
        :param extra_args: Extra arguments to pass to clang
        """

        if isinstance(source, Path):

            if not source.is_file():
                raise FileNotFoundError(f"{source} not found")

            source = source.read_text()

        if (
            arch == ClangArch.NONE
            and vendor == ClangVendor.NONE
            and os == ClangOS.NONE
            and environment == ClangEnvironment.NONE
        ):
            arch, vendor, os, environment = self.triple()

        triple_arg = "-".join(
            map(
                lambda tc: tc.value,
                filter(
                    lambda tc: tc != ClangArch.NONE, (arch, vendor, os, environment)
                ),
            )
        )

        args = [
            str(self.clang.resolve()),
            "-target",
            triple_arg,
            "-c",
            "-emit-llvm",
            "-x",
            "c",
            "-o",
            # Output to stdout
            "-",
            *(extra_args or []),
            # Input from stdin
            "-",
        ]

        try:
            bitcode = run(
                args, input=source.encode("utf-8"), capture_output=True, check=True
            ).stdout
        except CalledProcessError as e:
            logger.error("Compilation failed with error(s):")

            for line in e.stderr.decode("utf-8").splitlines():
                logger.error(line)

            raise CompilationError(f"Unable to produce bitcode from: {source}") from e

        if not bitcode:
            raise CompilationError(f"Unable to produce bitcode from: {source}")

        return bitcode

    def opt_bitcode(
        self,
        source: Union[bytes, Path],
        passes: List[str],
        libs: Optional[List[Path]] = None,
        extra_args: Optional[List[str]] = None,
    ) -> bytes:
        """
        Optimize bitcode using some set of passes

        :param source: The bitcode to optimize, either from a file or raw bytes
            from `emit_bitcode`
        :param passes: The passes to run on the bitcode
        :param libs: The pass libraries to load before running the passes
        :param extra_args: Extra arguments to pass to opt
        """

        if isinstance(source, Path):

            if not source.is_file():
                raise FileNotFoundError(f"{source} not found")

            source = source.read_bytes()

        load_args = list(
            *chain(map(lambda l: ["-load-pass-plugin", str(l.resolve())], libs)),
        )

        args = [
            str(self.opt.resolve()),
            *load_args,
            f"-passes={','.join(passes)}",
            *(extra_args or []),
            "-o",
            "-",
            "-f",
            # Input from stdin
            "-",
        ]

        try:
            bitcode = run(args, input=source, capture_output=True, check=True).stdout
        except CalledProcessError as e:
            logger.error("Optimization failed with error(s):")

            for line in e.stderr.decode("utf-8").splitlines():
                logger.error(line)

            raise CompilationError("Unable to optimize bitcode") from e

        if not bitcode:
            raise CompilationError("Unable to optimize bitcode")

        return bitcode

    def emit_binary(
        self,
        source: Union[bytes, Path],
        arch: ClangArch = ClangArch.NONE,
        vendor: ClangVendor = ClangVendor.NONE,
        os: ClangOS = ClangOS.NONE,
        environment: ClangEnvironment = ClangEnvironment.NONE,
        extra_args: Optional[List[str]] = None,
    ) -> bytes:
        """
        Emit bitcode from a source file

        :param source: The source file or raw bitcode to compile to binary
        :param arch: The architecture to compile for
        :param vendor: The vendor to compile for
        :param os: The OS to compile for
        :param environment: The environment to compile for
        :param extra_args: Extra arguments to pass to clang
        """

        if isinstance(source, Path):

            if not source.is_file():
                raise FileNotFoundError(f"{source} not found")

            source = source.read_bytes()

        if (
            arch == ClangArch.NONE
            and vendor == ClangVendor.NONE
            and os == ClangOS.NONE
            and environment == ClangEnvironment.NONE
        ):
            arch, vendor, os, environment = self.triple()

        triple_arg = "-".join(
            map(
                lambda tc: tc.value,
                filter(
                    lambda tc: tc != ClangArch.NONE, (arch, vendor, os, environment)
                ),
            )
        )

        output_file = NamedTemporaryFile()
        output_file_path = Path(output_file.name).resolve()

        args = [
            str(self.clang.resolve()),
            "-target",
            triple_arg,
            "-Oz",
            "-x",
            "ir",
            "-o",
            output_file.name,
            # TODO: Is there a better way for this?
            *(extra_args or []),
            # Input from stdin
            "-",
        ]

        try:
            run(args, input=source, capture_output=True, check=True)

            if not output_file_path.is_file():
                raise FileNotFoundError(f"{output_file_path} not found")

            binary = output_file_path.read_bytes()
        except CalledProcessError as e:
            logger.error("Compilation failed with error(s):")

            for line in e.stderr.decode("utf-8").splitlines():
                logger.error(line)

            raise CompilationError("Unable to produce binary") from e
        finally:
            output_file.close()

        return binary
