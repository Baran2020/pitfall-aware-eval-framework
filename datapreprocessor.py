from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import uuid
from ObfuscationEngine import ObfuscationEngine
from InjectLabelEngine_P2 import InjectLabelEngine
import random
import os
import re
import json
import metadataregistrar
from copy import deepcopy
from pathlib import Path

import subprocess
import shutil
#from Obfuscation_Engine_P4 import ObfuscationEngineP4

class Dispatcher:
    def __init__(self, dataset_path, project_id, dataset_id, dataset_type="SourceCode", tool_path=None, user_id=None, labels_path=None):
        self.dataset_path = dataset_path
        self.project_id   = project_id
        self.dataset_id   = dataset_id
        self.dataset_type = dataset_type
        self.tool_path    = tool_path
        self.user_id      = user_id
        self.dataset      = None
        '''
        self.dataset_path_min = dataset_path
        self.dataset_path_max = dataset_path
        self.dataset_path_4   = dataset_path
        '''
        base_for_p3 = self.parent_dir(dataset_path, 1)
        self.dataset_path_min = base_for_p3
        self.dataset_path_max = base_for_p3
        # single shared parent dir for all P2 (label-noise) variants; each
        # noise level gets its own subfolder under this, created on demand
        # inside inject_label_engine_p2(). Previously there were four
        # separate attributes here (dataset_path_P2_D1/D2/D3, dataset_P2_path_D4)
        # with inconsistent names that didn't match what inject_label_engine_p2
        # actually referenced further down (dataset_path__P2_D3 / __P2_D4,
        # double underscore) -> AttributeError as soon as that method ran.
        self.dataset_path_p2_base = base_for_p3
        # optional explicit labels.txt path for the ORIGINAL clean labels used
        # as input to the P2/P3/P4/P8 engines. Previously this fell back to a
        # literal hardcoded to TL31's ReCheckermaster/train_data/user path --
        # Mainframework.py never passes labels_path explicitly, so every
        # dataset run silently used TL31's labels regardless of which
        # dataset_path was actually registered. Default is now derived from
        # dataset_path itself (labels.txt living alongside it, same
        # convention TL31's "user" dataset already follows), so pointing
        # Mainframework.py at a different dataset_path picks up that
        # dataset's own labels.txt instead of always TL31's.
        self.labels_path = labels_path or os.path.join(dataset_path, "labels.txt")
        self.dataset_path_4   = base_for_p3
                #*************************************************************************************************
    def parent_dir(self, p: str, steps: int = 1) -> str:
        x = Path(p)
      
        if x.suffix:   # e.g., .txt .sol
            x = x.parent
        for _ in range(steps):
            x = x.parent
        return str(x)

        #*************************************************************************************************
    def run(self, dataset_id):
        print("start run function in Dispatcher ...............................")
        # Load dataset into self.dataset
        self.dataset = metadataregistrar.load_dataset(dataset_id)
        if not self.dataset:
            print("[WARN] Dataset is empty, nothing to process.")
            return []

        engine_map = {
            #self.inject_label_engine_p2: "inject_label_P2",
            #self.obfuscation_engine_p3: "obf_P3",
            #self.obfuscation_engine_P4: "obf_P4"
            #self.skew_synthesis_engine: "skew_synth_P8"
        }

        results = []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(func): name for func, name in engine_map.items()}

            for fut in as_completed(futures):
                engine_name = futures[fut]
                try:
                    engine_outputs = fut.result()
                except Exception as e:
                    print(f"[ERROR] Engine {engine_name} failed: {e}")
                    continue

                if not engine_outputs:
                    print(f"[WARN] Engine {engine_name} returned nothing; skipping.")
                    continue

                if isinstance(engine_outputs, dict):
                    engine_outputs = [engine_outputs]
                elif not isinstance(engine_outputs, list):
                    print(f"[WARN] Engine {engine_name} returned invalid type; skipping.")
                    continue

                
                for out in engine_outputs:
                    ds_name = out.get("dataset_name")
                    ds_path = out.get("dataset_path")
                    ds_content = out.get("dataset_content")  # optional

                    if not ds_name:
                        print(f"[WARN] Engine {engine_name} returned unnamed dataset; skipping.")
                        continue

                    
                    if ds_path:
                        
                        try:
                            metadata = metadataregistrar.create_metadata_dataset(
                                dataset_path=os.path.dirname(ds_path) if os.path.isfile(ds_path) else ds_path,
                                project_id=self.project_id,
                                dataset_type=self.dataset_type,
                                dataset_name=ds_name,
                                dataset_file=os.path.basename(ds_path),
                                input_type="text"
                            )
                            metadataregistrar.save_metadata_dataset(metadata)
                            results.append({"dataset_name": ds_name, "dataset_path": ds_path, "engine": engine_name})
                            print(f"[Dispatcher] Registered dataset (pre-saved) {ds_name} -> {ds_path}")
                        except Exception as e:
                            print(f"[ERROR] Failed to save metadata for pre-saved {ds_name}: {e}")
                        continue

                   
                    if ds_content:
                        try:
                            
                            saved_path = metadataregistrar.save_dataset(
                                self.dataset_path,  
                                ds_content,
                                self.project_id,
                                ds_name
                            )
                            print(output_path)
                            metadata = metadataregistrar.create_metadata_dataset(
                                dataset_path=saved_path,
                                project_id=self.project_id,
                                dataset_type=self.dataset_type,
                                dataset_name=ds_name,
                                dataset_file=os.path.basename(ds_path),
                                input_type="text"
                            )
                            metadataregistrar.save_metadata_dataset(metadata)
                            results.append({"dataset_name": ds_name, "dataset_path": saved_path, "engine": engine_name})
                            print(f"[Dispatcher] Saved+Registered dataset {ds_name} -> {saved_path}")
                        except Exception as e:
                            print(f"[ERROR] Failed to save/register dataset {ds_name}: {e}")
                        continue

                    
                    print(f"[WARN] Engine {engine_name} returned dataset entry without path or content: {out}")

        print(f"[Dispatcher] Finished all engines. Total successful datasets: {len(results)}")
        return results



#**************************************************************************************************
    # noise levels required by the P2 protocol (thesis Section 5.5.2): five
    # stages of symmetric, per-class label-swap noise: 0.5%, 1%, 1.5%, 2%,
    # 2.5%. Each level is sampled independently from the ORIGINAL clean
    # labels (never from a previously-noised version), using a distinct,
    # reproducible seed per level -- both properties are already implemented
    # by InjectLabelEngine_P2.inject_label(); this dispatcher method just has
    # to call it correctly and once per level.
    P2_NOISE_LEVELS = [0.005, 0.01, 0.015, 0.02, 0.025]
    P2_SEED_BASE = 1000
    # kept equal to the ReChecker baseline's repeat count (already run 10x)
    # so P2 noise-level results are directly comparable in the thesis
    P2_N_REPEATS = 10

    def inject_label_engine_p2(self):
        print("start inject_label_engine_p2 function in datapreprocessor  ...............")

        if not self.dataset:
            print("Dataset is empty. Nothing to process.")
            return []

        inject_label_enginep2 = InjectLabelEngine()

        # The ORIGINAL, clean labels are what gets noised at each level. The
        # previous version of this method never loaded a labels file at all;
        # it tried to call inject_label(content) directly on each contract's
        # SOURCE CODE, which is wrong on two counts: (1) InjectLabelEngine.
        # inject_label() takes a {filename: label} dict plus a fraction and a
        # seed, not a source-code string, so this raised a TypeError before
        # doing anything; and (2) P2 is a LABEL-noise test -- the whole point
        # (Section 5.5.2) is that contract source code stays byte-for-byte
        # identical across variants and only the ground-truth label file
        # changes, mirroring how P3 keeps semantics fixed and only rewrites
        # the pragma version string.
        try:
            original_labels = inject_label_enginep2.load_labels(self.labels_path)
        except Exception as e:
            print(f"[P2][ERROR] Failed to load original labels from {self.labels_path}: {e}")
            return []

        if not original_labels:
            print(f"[P2][WARN] No labels found in {self.labels_path}; nothing to inject noise into.")
            return []

        # contracts themselves are never modified for P2, so we only need one
        # copy of the dataset content, reused (unchanged) for every variant.
        dataset_copy = deepcopy(self.dataset)
        sol_items = [
            item for item in dataset_copy
            if isinstance(item, dict)
            and item.get("filename")
            and item.get("content") is not None
            and item["filename"].endswith(".sol")
        ]

        if not sol_items:
            print("[P2][WARN] No .sol items found in dataset; nothing to process.")
            return []

        from FolderdatasetTOtext import generate_txt

        datasets_return = []

        for level_index, fraction in enumerate(self.P2_NOISE_LEVELS, start=1):
            for rep in range(1, self.P2_N_REPEATS + 1):
                variant_name = f"P2_noise_{fraction * 100:g}pct_rep{rep}"
                seed = self.P2_SEED_BASE + (level_index * 100) + rep

                noisy_labels, swap_info = inject_label_enginep2.inject_label(
                    original_labels, fraction, seed
                )

                try:
                    variant_path = metadataregistrar.save_dataset(
                        self.dataset_path_p2_base,
                        sol_items,
                        self.project_id,
                        variant_name
                    )
                    print(variant_path)
                except Exception as e:
                    print(f"[P2][ERROR] Failed to save contracts for {variant_name}: {e}")
                    continue

                noisy_labels_path = os.path.join(variant_path, f"{variant_name}_labels.txt")
                try:
                    inject_label_enginep2.save_labels(noisy_labels, noisy_labels_path)
                except Exception as e:
                    print(f"[P2][ERROR] Failed to save noisy labels for {variant_name}: {e}")
                    continue

                try:
                    txt_path = generate_txt(
                        sol_dir=variant_path,
                        labels_path=noisy_labels_path,
                        output_path=os.path.join(variant_path, f"{variant_name}.txt")
                    )
                except Exception as e:
                    print(f"[P2][ERROR] Failed to generate manifest for {variant_name}: {e}")
                    continue

                print(
                    f"[P2] {variant_name} generated -> {txt_path} "
                    f"(fraction={fraction}, seed={seed}, pos_swapped={swap_info['n_positive_swapped']}, "
                    f"neg_swapped={swap_info['n_negative_swapped']})"
                )

                datasets_return.append({"dataset_name": variant_name, "dataset_path": txt_path})

        print("end inject_label_engine_p2 function *********************************************")

        return datasets_return

#**************************************************************************************************

    def obfuscation_engine_p3(self):
        print("start obfuscation_engine_P3 function in datapreprocessor  ...............") 

        if not self.dataset:
            print("Dataset is empty. Nothing to process.")
            #return None  

        obfuscation_engine_P3  = ObfuscationEngine()
        updated_dataset_min = []
        updated_dataset_max = []
        datasets_return=[]
        dataset_copy = deepcopy(self.dataset)

        # Tracks contracts where the compile-verified real minimum version
        # equals the contract's own already-declared minimum -- for those,
        # rewriting the pragma is a no-op (the P3-min output is byte-for-
        # byte identical to the original), so they are NOT a real
        # perturbation and must be reported separately rather than silently
        # counted as "processed" the same as genuinely downgraded ones.
        no_real_change_count = 0
        real_change_count = 0
        source_items_seen = 0
        no_real_change_filenames = []

        for item in dataset_copy:

            if not isinstance(item, dict):
                print(f"[OE][WARN] Unexpected dataset item format, skipping: {repr(item)[:200]}")
                continue

            filename = item.get("filename")
            content = item.get("content")
            if filename is None or content is None:
                print(f"[OE][WARN] Missing filename or content, skipping item: {item}")
                continue

            if not filename.endswith(".sol") :
                continue



            #print(f"[OE][WARN] {Oengine.is_source_code(content)}  content: {content}")
            is_source, version, min_ver, max_ver =  obfuscation_engine_P3.is_source_code(content)


            if is_source:
                print(f"[OE] Processing source code, Solidity version: {version}")

                verified_min = obfuscation_engine_P3.get_verified_min_version(content)
                source_items_seen += 1
                if verified_min["is_real_change"]:
                    real_change_count += 1
                    updated_content_min = obfuscation_engine_P3.update_pragma(content, verified_min["real_min"])
                else:
                    # Real minimum == the contract's own declared minimum
                    # (or couldn't be determined) -- no genuine downgrade
                    # exists, so the min variant is left unchanged rather
                    # than rewritten to a version that wouldn't differ from
                    # baseline.
                    no_real_change_count += 1
                    no_real_change_filenames.append(filename)
                    updated_content_min = content

                updated_content_max = obfuscation_engine_P3.update_pragma(content, max_ver)

            else:
                print("[OE] Detected bytecode, applying different processing")
                updated_content_min  = content
                updated_content_max  = content

            updated_dataset_min.append({
            "filename": filename,
            "content": updated_content_min
             })


            updated_dataset_max.append({
            "filename": filename,
            "content": updated_content_max
             })

        if source_items_seen:
            pct_no_change = no_real_change_count / source_items_seen * 100
            print(f"[P3][min-version stats] source contracts processed: {source_items_seen}")
            print(f"[P3][min-version stats] real downgrade applied: {real_change_count} "
                  f"({real_change_count / source_items_seen * 100:.1f}%)")
            print(f"[P3][min-version stats] no real change possible (already at declared floor): "
                  f"{no_real_change_count} ({pct_no_change:.1f}%)")
            if no_real_change_filenames:
                print(f"[P3][min-version stats] no-real-change contracts "
                      f"({no_real_change_count}): {no_real_change_filenames}")
            try:
                stats_path = os.path.join(self.dataset_path_min, "p3_min_version_stats.json")
                with open(stats_path, "w", encoding="utf8") as f:
                    json.dump({
                        "source_contracts_processed": source_items_seen,
                        "real_change_count": real_change_count,
                        "no_real_change_count": no_real_change_count,
                        "no_real_change_pct": pct_no_change,
                        "no_real_change_filenames": no_real_change_filenames,
                    }, f, indent=2)
                print(f"[P3][min-version stats] written to {stats_path}")
            except Exception as e:
                print(f"[OE][ERROR] Failed to write p3_min_version_stats.json: {e}")

        try:
                self.dataset_path_min = metadataregistrar.save_dataset(
                    self.dataset_path_min,
                    updated_dataset_min,
                    self.project_id,
                    "P3_updated_version_min"
                  
                              )
                print(self.dataset_path_min)
        except Exception as e:
                print(f"[OE][ERROR] Failed to save updated dataset_P3_min: {e}")

        try:
                self.dataset_path_max = metadataregistrar.save_dataset(
                    self.dataset_path_max,
                    updated_dataset_max,
                    self.project_id,
                    "P3_updated_version_max"
                                       
                    )
                print(self.dataset_path_max)
        except Exception as e:
                print(f"[OE][ERROR] Failed to save updated dataset_P3_max: {e}")
        '''
        datasets_return = [
        {"dataset_name": "P3_updated_version_min", "dataset_path": self.dataset_path_min},
        {"dataset_name": "P3_updated_version_max", "dataset_path": self.dataset_path_max}]        
        
        return datasets_return
        '''
        from FolderdatasetTOtext import generate_txt

        txt_path_min = generate_txt(
            sol_dir=self.dataset_path_min,
            labels_path=self.labels_path,
            output_path=os.path.join(self.dataset_path_min, "P3_updated_version_min.txt")
        )

        txt_path_max = generate_txt(
            sol_dir=self.dataset_path_max,
            labels_path=self.labels_path,
            output_path=os.path.join(self.dataset_path_max, "P3_updated_version_max.txt")
        )

        print(f"[P3] txt_min generated: {txt_path_min}")
        print(f"[P3] txt_max generated: {txt_path_max}")
        print("end obfuscation_engine_p3 function *********************************************")

        return [
            {"dataset_name": "P3_updated_version_min", "dataset_path": txt_path_min},
            {"dataset_name": "P3_updated_version_max", "dataset_path": txt_path_max}
        ]
        
        

#**************************************************************************************************
    

    def obfuscation_engine_P4(self):
        print("start obfuscation_engine_P4 function in datapreprocessor ...............")

        if not self.dataset:
            print("[P4] Dataset is empty. Nothing to process.")
            return []

        output_dir = os.path.join(self.dataset_path_4, "P4_obfuscated")
        os.makedirs(output_dir, exist_ok=True)

        # Previously this listed self.dataset_path on disk (os.listdir) and
        # expected one loose .sol file per contract. That only holds for
        # input_type=="folder" datasets. P2/P3/P8 all instead iterate
        # self.dataset -- the list metadataregistrar.load_dataset() already
        # built correctly for whatever input_type the dataset actually is
        # (folder / text-manifest / excel / json). A manifest dataset (e.g.
        # this project's "user" dataset, input_type="text", contracts packed
        # inside user.txt) has no loose .sol files under dataset_path, so the
        # old os.listdir loop silently matched nothing, ran the obfuscator on
        # zero files, and produced an empty P4_obfuscated dataset that still
        # logged as if it succeeded. Iterating self.dataset fixes that for
        # every input_type, matching how P3 already does it.
        tmp_input_dir = os.path.join(output_dir, "_tmp_input")
        os.makedirs(tmp_input_dir, exist_ok=True)

        updated_content_p4 = []
        dataset_copy = deepcopy(self.dataset)

        for item in dataset_copy:
            if not isinstance(item, dict):
                print(f"[P4][WARN] Unexpected dataset item format, skipping: {repr(item)[:200]}")
                continue

            filename = item.get("filename")
            content = item.get("content")
            if filename is None or content is None:
                print(f"[P4][WARN] Missing filename or content, skipping item: {item}")
                continue

            if not filename.endswith(".sol") or filename.startswith("obf_"):
                continue

            # the external obfuscation tool (USTObfusSolToolmain/main.py) only
            # accepts file paths, so the in-memory content has to be
            # materialized to disk first -- there's no on-disk original to
            # point it at once the dataset isn't a plain folder.
            input_path = os.path.join(tmp_input_dir, filename)
            output_path = os.path.join(output_dir, f"obf_{filename}")
            os.makedirs(os.path.dirname(input_path), exist_ok=True)
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Processing {filename} ...")

            result = subprocess.run(
                ["python3", "main.py", input_path, output_path, "--all"],
                cwd="/mnt/f/LISTTOOL/Framework/obfuscation/USTObfusSolToolmain",
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"[ERROR] {filename}: {result.stderr}")
                continue

            with open(output_path, "r", encoding="utf-8") as f:
                obf_code = f.read()

            updated_content_p4.append({
                "filename": filename,
                "content": obf_code,
            })

        shutil.rmtree(tmp_input_dir, ignore_errors=True)

        # Guard against silently "succeeding" with an empty dataset -- this is
        # the actual gap that let 0-written/393-missing pass as success
        # before: nothing downstream checked whether any file made it through.
        if not updated_content_p4:
            print(f"[P4][ERROR] 0 of {len(dataset_copy)} dataset items were obfuscated "
                  f"(no matching .sol content, or every subprocess call failed) -- "
                  f"refusing to register an empty P4_obfuscated dataset.")
            return []

        try:
                self.dataset_path_obfuscated_p4 = metadataregistrar.save_dataset(
                    self.dataset_path_4 ,
                    updated_content_p4,
                    self.project_id,
                    "P4_obfuscated"

                    )
                print(self.dataset_path_obfuscated_p4)
        except Exception as e:
                print(f"[OE][ERROR] Failed to save dataset_obfuscated_p4: {e}")
                return []
        datasets_obfuscated_p4 = [
            {"dataset_name": "P4_obfuscated", "dataset_path": self.dataset_path_obfuscated_p4}]

        from FolderdatasetTOtext import generate_txt
        txt_path = generate_txt(
            sol_dir=output_dir,
            labels_path=self.labels_path,
            output_path=os.path.join(output_dir, "P4_obfuscated.txt")
        )
        print(f"[P4] txt generated: {txt_path}")
        self.dataset_path_txt_p4 = txt_path

        # return datasets_obfuscated_p4
        print("end obfuscation_engine_p4 function *********************************************")

        return [{"dataset_name": "P4_obfuscated", "dataset_path": txt_path}]
       
        





    '''def obfuscation_engine_P4(self):
        print("start obfuscation_engine_P4 function")

        if not self.dataset:
            print("Dataset is empty")
            return None

        updated_content_p4 = []

        output_dir = os.path.join(self.dataset_path_4, "datasets_obfuscated_p4")
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(self.dataset_path):

            if not filename.endswith(".sol"):
                continue

            input_path = os.path.join(self.dataset_path, filename)

            print(f"Processing {filename} ...")

            try:
                result = subprocess.run(
                    ["python3", "main.py", input_path, "--all"],
                    cwd="/mnt/f/LISTTOOL/Framework/obfuscation/USTObfusSolToolmain",
                    capture_output=True,
                    text=True,
                    check=True
                )

                obf_code = result.stdout

                updated_content_p4.append({
                    "filename": filename,
                    "content": obf_code
                })

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] {filename}")
                print(e.stderr)

        
        try:
            saved_path = metadataregistrar.save_dataset(
                output_dir,
                updated_content_p4,
                self.project_id,
                "P4_obfuscated"
            )

        except Exception as e:
            print(f"[OE][ERROR] save failed: {e}")
            return None

        return [{
            "dataset_name": "P4_obfuscated",
            "dataset_path": saved_path
        }]


  

     def obfuscation_engine_P4(self):
        print("start obfuscation_engine_P4")
        print("dataset_path:", self.dataset_path)

        OUTPUT_DIR = self.dataset_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        files = os.listdir(self.dataset_path)

        sol_files = [
            f for f in files
            if f.endswith(".sol") and not f.startswith("obf_")
        ]

        if not sol_files:
            print("[ERROR] No valid .sol files found")
            return None

        for filename in sol_files:
            input_path = os.path.join(self.dataset_path, filename)
            output_path = os.path.join(self.dataset_path, f"obf_{filename}")

            print(f"Processing {filename} ...")

            try:
                result = subprocess.run(
                    ["python3", "main.py", input_path, output_path, "--all"],
                    cwd="/mnt/f/LISTTOOL/Framework/obfuscation/USTObfusSolToolmain",
                    capture_output=True,
                    text=True,
                    check=True
                )

                print(result.stdout)

            except subprocess.CalledProcessError as e:
                print(f"[ERROR] {filename}")
                print(e.stderr)

        return [{
            "dataset_name": "P4_obfuscated",
            "dataset_path": OUTPUT_DIR
        }]
        '''
#**************************************************************************************************
# natural base rate +/- 2.5 and +/-5 percentage points -- NOT including
    # 0.0. The zero-offset point is just the "user" dataset itself, already
    # registered and already evaluated by the other tests; skew_synthesis_engine
    # only needs to build these four genuinely *skewed* variants.
    P8_BASE_RATE_OFFSETS = [-0.05, -0.025, 0.025, 0.05]
    P8_SEED_BASE = 8000
    P8_RATE_EPSILON = 1e-6

    @staticmethod
    def _p8_offset_suffix(offset):
        sign = "plus" if offset > 0 else "minus"
        # NOTE: no round() here -- round(2.5) == 2 in Python (banker's
        # rounding), which would silently rename the +/-2.5pct variants to
        # +/-2pct and break the match against test8.py's SPECTRUM_ORDER.
        return f"{sign}{abs(offset * 100):g}pct"

    @staticmethod
    def _p8_dup_filename(fn, dup_idx):
        # gives each oversampled duplicate its own on-disk name so the
        # variant folder holds one physical file per label-file entry,
        # same as every other engine here -- no file is ever looked up
        # more than once.
        p = Path(fn)
        return f"{p.stem}__dup{dup_idx}{p.suffix}"

    def skew_synthesis_engine(self):
        print("start skew_synthesis_engine function in datapreprocessor  ...............")

        if not self.dataset:
            print("Dataset is empty. Nothing to process.")
            return []

        inject_label_engine = InjectLabelEngine()

        try:
            original_labels = inject_label_engine.load_labels(self.labels_path)
        except Exception as e:
            print(f"[P8][ERROR] Failed to load original labels from {self.labels_path}: {e}")
            return []

        if not original_labels:
            print(f"[P8][WARN] No labels found in {self.labels_path}; nothing to skew.")
            return []

        dataset_copy = deepcopy(self.dataset)
        sol_items = [
            item for item in dataset_copy
            if isinstance(item, dict)
            and item.get("filename")
            and item.get("content") is not None
            and item["filename"].endswith(".sol")
            and item["filename"] in original_labels
        ]

        if not sol_items:
            print("[P8][WARN] No labelled .sol items found in dataset; nothing to process.")
            return []

        content_by_filename = {item["filename"]: item["content"] for item in sol_items}
        positive_files = [fn for fn in content_by_filename if original_labels[fn] == 1]
        negative_files = [fn for fn in content_by_filename if original_labels[fn] == 0]

        n_pos, n_neg = len(positive_files), len(negative_files)
        total0 = n_pos + n_neg

        if n_pos == 0 or n_neg == 0:
            print(f"[P8][WARN] need both classes present to skew the base rate "
                  f"(n_pos={n_pos}, n_neg={n_neg}); nothing to process.")
            return []

        natural_rate = n_pos / total0
        print(f"[P8] natural base rate = {natural_rate:.4f} ({n_pos} vulnerable / {total0} total)")

        base_labels = {fn: original_labels[fn] for fn in positive_files + negative_files}

        # per-variant saved folder, keyed by variant name -- generalises the
        # self.dataset_path_min / self.dataset_path_max attributes P3 uses
        # for its two variants to the variants P8 needs.
        self.dataset_path_p8 = {}

        datasets_return = []

        for level_index, offset in enumerate(self.P8_BASE_RATE_OFFSETS, start=1):
            target_rate = natural_rate + offset
            target_rate = min(max(target_rate, self.P8_RATE_EPSILON), 1 - self.P8_RATE_EPSILON)

            variant_name = f"P8_base_rate_{self._p8_offset_suffix(offset)}"
            seed = self.P8_SEED_BASE + level_index
            rng = random.Random(seed)

            extra_items = []
            variant_labels = dict(base_labels)  # unique filenames only, so far
            n_extra_pos = n_extra_neg = 0

            if target_rate > natural_rate:
                # need relatively MORE positives -> oversample (with
                # replacement) from the vulnerable class only
                n_extra_pos = max(round((target_rate * total0 - n_pos) / (1 - target_rate)), 0)
                for dup_idx, fn in enumerate(rng.choices(positive_files, k=n_extra_pos), start=1):
                    new_fn = self._p8_dup_filename(fn, dup_idx)
                    extra_items.append({"filename": new_fn, "content": content_by_filename[fn]})
                    variant_labels[new_fn] = 1

            else:
                # need relatively FEWER positives -> oversample (with
                # replacement) from the safe class only, diluting the
                # positive proportion
                n_extra_neg = max(round(n_pos / target_rate - total0), 0)
                for dup_idx, fn in enumerate(rng.choices(negative_files, k=n_extra_neg), start=1):
                    new_fn = self._p8_dup_filename(fn, dup_idx)
                    extra_items.append({"filename": new_fn, "content": content_by_filename[fn]})
                    variant_labels[new_fn] = 0

            variant_items = sol_items + extra_items  # every physical file this variant needs, unique names

            achieved_pos = sum(1 for lbl in variant_labels.values() if lbl == 1)
            achieved_total = len(variant_labels)
            achieved_rate = achieved_pos / achieved_total if achieved_total else 0

            try:
                variant_path = metadataregistrar.save_dataset(
                    self.dataset_path_p2_base,
                    variant_items,
                    self.project_id,
                    variant_name
                )
            except Exception as e:
                print(f"[P8][ERROR] Failed to save contracts for {variant_name}: {e}")
                continue

            self.dataset_path_p8[variant_name] = variant_path

            variant_labels_path = os.path.join(variant_path, f"{variant_name}_labels.txt")
            try:
                inject_label_engine.save_labels(variant_labels, variant_labels_path)
            except Exception as e:
                print(f"[P8][ERROR] Failed to save labels for {variant_name}: {e}")
                continue

            try:
                from FolderdatasetTOtext import generate_txt
                txt_path = generate_txt(
                    sol_dir=variant_path,
                    labels_path=variant_labels_path,
                    output_path=os.path.join(variant_path, f"{variant_name}.txt")
                )
            except Exception as e:
                print(f"[P8][ERROR] Failed to generate manifest for {variant_name}: {e}")
                continue

            print(
                f"[P8] {variant_name} -> {txt_path}  "
                f"target_rate={target_rate:.4f}  achieved_rate={achieved_rate:.4f}  "
                f"({achieved_pos}/{achieved_total}, +{n_extra_pos} pos / +{n_extra_neg} neg duplicated files)"
            )

            datasets_return.append({"dataset_name": variant_name, "dataset_path": txt_path})

        print("end skew_synthesis_engine function *********************************************")
        return datasets_return