import re
import json
import solcx
import os
from solcx import compile_standard
from web3 import Web3
import subprocess

import pragma_compatibility_checker

class ObfuscationEngine:

    def get_version_bounds(self, version):
   
        print("start get_version_bounds function in Obfuscation_Engine.py .................")

        max_version = [7, 2, 6, 26, 17, 12, 6, 28]  # max patch per minor (index = minor-1 for major=0)

        raw = version.strip()
        cleaned = raw.replace("^", "").replace("~", "").strip()

        def _max_patch_for(major: int, minor: int):
            if major == 0:
                idx = minor - 1
            else:
                idx = major - 1
            if 0 <= idx < len(max_version):
                return max_version[idx]
            return 0

        # 1) Caret operator
        if raw.startswith("^"):
            major, minor, patch = [int(x) for x in cleaned.split('.')]
            min_ver = f"{major}.{minor}.0"
            max_patch = _max_patch_for(major, minor)
            max_ver = f"{major}.{minor}.{max_patch}"
            print(f"min version: {min_ver}, max version: {max_ver}")
            print("end get_version_bounds function **********************************")
            return min_ver, max_ver

        # 2) Explicit ranges
        parts = re.findall(r"([<>]=?)\s*(\d+\.\d+\.\d+)", raw)
        lower = None
        upper = None
        for op, ver in parts:
            if op in (">=", ">"):
                lower = ver
            elif op in ("<=", "<"):
                upper = ver

        if lower and upper:
            major_l, minor_l, _ = [int(x) for x in lower.split('.')]
            major_u, minor_u, _ = [int(x) for x in upper.split('.')]
            min_ver = f"{major_l}.{minor_l}.0"

            # Include all of previous minor if upper is < major_u.minor_u.0
            if major_u == 0:
                included_minor = minor_u - 1
                max_patch = _max_patch_for(0, included_minor)
                max_ver = f"0.{included_minor}.{max_patch}"
            else:
                included_major = major_u - 1
                max_patch = _max_patch_for(included_major, 0)
                max_ver = f"{included_major}.0.{max_patch}"

            print(f"min version: {min_ver}, max version: {max_ver}")
            print("end get_version_bounds function **********************************")
            return min_ver, max_ver

        # 3) Only lower bound
        if lower and not upper:
            major_l, minor_l, _ = [int(x) for x in lower.split('.')]
            min_ver = f"{major_l}.{minor_l}.0"
            max_patch = _max_patch_for(major_l, minor_l)
            max_ver = f"{major_l}.{minor_l}.{max_patch}"
            print(f"min version: {min_ver}, max version: {max_ver}")
            print("end get_version_bounds function **********************************")
            return min_ver, max_ver

        # 4) Only upper bound
        if upper and not lower:
            major_u, minor_u, _ = [int(x) for x in upper.split('.')]
            if major_u == 0:
                included_minor = minor_u - 1
                max_patch = _max_patch_for(0, included_minor)
                min_ver = f"0.0.0"
                max_ver = f"0.{included_minor}.{max_patch}"
            else:
                included_major = major_u - 1
                max_patch = _max_patch_for(included_major, 0)
                min_ver = f"0.0.0"
                max_ver = f"{included_major}.0.{max_patch}"
            print(f"min version: {min_ver}, max version: {max_ver}")
            print("end get_version_bounds function **********************************")
            return min_ver, max_ver

        # 5) Single version
        m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)\s*$", cleaned)
        if m:
            major_s, minor_s, patch_s = [int(x) for x in m.groups()]
            min_ver = f"{major_s}.{minor_s}.0"
            max_patch = _max_patch_for(major_s, minor_s)
            max_ver = f"{major_s}.{minor_s}.{max_patch}"
            print(f"min version: {min_ver}, max version: {max_ver}")
            print("end get_version_bounds function **********************************")
            return min_ver, max_ver

        # Fallback
        min_ver = "0.8.0"
        max_ver = "0.8.28"
        print(f"min version: {min_ver}, max version: {max_ver}")
        print("end get_version_bounds function **********************************")
        return min_ver, max_ver

    # **************************************************************************************
    def is_source_code(self, content):
        print("start is_source_code   function in ObfuscationEngin.py .................")

        # Bytecode is a long hex blob (optionally 0x-prefixed) with no
        # whitespace/keywords at all -- this is the ONLY case that should
        # be treated as "not source". Everything else (full contracts,
        # or fragments with neither pragma nor a contract declaration) is
        # still Solidity source, just structurally incomplete.
        bytecode_pattern = r'^\s*(0x)?[0-9a-fA-F]{100,}\s*$'
        if re.match(bytecode_pattern, content):
            print("end is_source_code function in ObfuscationEngine.py --detected bytecode-- **********************************")
            return False, "0.8.28", "0.8.0", "0.8.28"

        pragma_pattern = r'pragma\s+solidity\s+([^;]+);'
        match = re.search(pragma_pattern, content, re.IGNORECASE)

        if match:
            version = match.group(1).strip()
            version_without_caret = version.lstrip("^")
            min_version, max_version = self.get_version_bounds(version_without_caret)
            print(f"end is_source_code function in ObfuscationEngine.py  , min_version:{min_version},max_version:{max_version}  **********************************")
            return True, version_without_caret, min_version, max_version

        # No pragma -- whether or not a `contract X {` declaration is present
        # (full contracts and slicing fragments both fall here), there is no
        # version info recoverable from the text, so we fall back to the same
        # default range regardless.
        min_version = "0.8.0"
        max_version = "0.8.28"
        version_without_caret = "0.8.28"
        print("end is_source_code function in ObfuscationEngine.py --no pragma is found  --- **********************************")
        return True, version_without_caret, min_version, max_version
    # **************************************************************************************
    
    def update_pragma(self, content, version):
        print("start update_pragma   function.................")
        # Remove the caret (^) if present
        version_without_caret = version.lstrip("^")
        pragma_pattern = r'pragma\s+solidity\s+[^;]+;'

        # Replace pragma line with the new version
        if re.search(pragma_pattern, content, re.IGNORECASE):
            updated_content = re.sub(
                r'pragma\s+solidity\s+[^;]+;',
                f'pragma solidity {version_without_caret};',
                content
            )
        else:
            # no pragma present (fragment/slicing case) -- insert one instead
            # of silently no-op'ing via re.sub
            updated_content = f'pragma solidity {version_without_caret};\n' + content
    
        print("end update_pragma   function **************************")
        return updated_content
    #***************************************************************************************

    def get_verified_min_version(self, content):
        """
        Real, compile-verified replacement for get_version_bounds()'s "min"
        side: get_version_bounds() computes the min pragma by zeroing the
        declared version's patch number (e.g. "^0.4.24" -> "0.4.0"), with no
        regard for whether the contract's code actually uses language
        features introduced after that floor (require/revert/assert were
        added in solc 0.4.10) -- confirmed separately to produce a
        P3_updated_version_min dataset where 57.5% of records (1404/2457 on
        the `user` dataset) failed to compile at all.

        Returns the dict from pragma_compatibility_checker.
        check_min_compatibility(): {declared_min, real_min, is_real_change}.
        Callers (see datapreprocessor.obfuscation_engine_p3) should only
        rewrite the pragma to `real_min` when `is_real_change` is True --
        when it's False, the contract's own declared version is already its
        real floor, and P3's "min" variant would be byte-for-byte identical
        to the original for that contract, so it isn't a real perturbation.
        """
        print("start get_verified_min_version function in ObfuscationEngine.py .................")
        result = pragma_compatibility_checker.check_min_compatibility(content)
        print(f"declared_min: {result['declared_min']}, real_min: {result['real_min']}, "
              f"is_real_change: {result['is_real_change']}")
        print("end get_verified_min_version function **********************************")
        return result
    #***************************************************************************************

        #***********************************************************************************
        
    def ProcessDataset(self, dataset_path, tool_path):
        outputs = []
        total_files = 0
        success = 0

        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(".sol"):
                    total_files += 1
                    file_path = os.path.join(root, file)

                    print(f"Processing: {file_path}")

                    obf = self.RunObfuscation(file_path, tool_path)

                    if obf and obf["returncode"] == 0:
                        outputs.append(obf["stdout"])
                        success += 1
                    else:
                        print("ERROR in:", file_path)
                        if obf:
                            print(obf["stderr"])

        return outputs, total_files, success
    #****************************************************************************************
    '''
    def Obfuscation_p4(self, data_path):
        print("start Obfuscation_p4   function.................")
        print("data_path",data_path)
       
        ObfEngin_path =  "/mnt/f/LISTTOOL/Framework/obfuscation/USTObfusSolToolmain"
        data_path="/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/user/temptest4"
        try:
            result = subprocess.run(
                ["python3", "main.py", "--input", "/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/user/temptest4"],
                cwd=ObfEngin_path,
                capture_output=True,
                text=True
            )

        return  OutputFile = "/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/obf_contracts.txt"
        print("end Obfuscation_p4  function in ObfuscationEngin.py **************************")
      
    '''    