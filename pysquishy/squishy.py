"""
Wrapper code for squishy library
"""


from pathlib import Path
from typing import Dict, Union
from logging import getLogger

from lief import parse

from pysquishy.clang import (
    ClangArch,
    ClangEnvironment,
    ClangHelper,
    ClangOS,
    ClangVendor,
)
from pysquishy.libwrap.wrapper import LIBSQUISHY_LIB


logger = getLogger(__name__)


class Squishy:
    """
    Wrapper class for squishy library
    """

    @classmethod
    def extract_main(cls, binary: Union[bytes, Path]) -> bytes:
        """
        Extract the main function from a binary

        :param binary: Binary to extract the main function from. Must have
            a symbol for main to work.
        """

        if isinstance(binary, Path):
            if not binary.is_file():
                raise FileNotFoundError(f"Binary {binary} not found.")

            binary = binary.read_bytes()

        elf_binary = parse(binary)

        syms: Dict[str, int] = {}

        for sym in elf_binary.symbols:
            if isinstance(sym.value, int):
                syms[sym.name] = sym.value

        text_offset = 0

        for sec in elf_binary.sections:
            if sec.name == ".text":
                text_offset = sec.offset

        main_addr = syms.get("main")

        if not isinstance(main_addr, int):
            raise Exception("Main function not found.")

        assert isinstance(main_addr, int)  # Type checking assertion

        next_sym = sorted(
            filter(lambda v: v > main_addr, syms.values()),
            key=lambda v: v - main_addr,
        )[0]
        main_size = next_sym - main_addr

        blob = bytes(elf_binary.get_content_from_virtual_address(main_addr, main_size))

        return blob

    def compile(
        self,
        code: Union[Path, str],
        arch: ClangArch = ClangArch.NONE,
        vendor: ClangVendor = ClangVendor.NONE,
        os: ClangOS = ClangOS.NONE,
        environment: ClangEnvironment = ClangEnvironment.NONE,
    ) -> bytes:
        """
        Compile a file or string of C code into a callable blob

        :param code: Code to compile. Can be a string or a path to a file
            containing C code.
        :param arch: Architecture to compile for.
        :param vendor: Vendor to compile for.
        :param os: Operating system to compile for.
        :param environment: Environment to compile for.
        """

        if isinstance(code, Path):
            code = code.read_text()

        logger.debug(f"Compile requested for:")
        for i, line in enumerate(code.splitlines()):
            logger.debug(f"{i:04}: {line}")

        clang_helper = ClangHelper()
        unopt_bitcode = clang_helper.emit_bitcode(code, arch, vendor, os, environment, extra_args=["-masm=intel"])
        logger.debug(f"Produced unoptimized bitcode of length {len(unopt_bitcode)}")
        opt_bitcode = clang_helper.opt_bitcode(
            unopt_bitcode, ["squishy-inline"], [LIBSQUISHY_LIB]
        )
        logger.debug(f"Produced optimized bitcode of length {len(opt_bitcode)}")
        binary = clang_helper.emit_binary(opt_bitcode, arch, vendor, os, environment)
        logger.debug(f"Produced binary of size {len(binary)}")
        blob = self.extract_main(binary)
        logger.debug(f"Produced blob of size {len(blob)}")
        return blob
