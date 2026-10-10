import metadataregistrar
#from datapreprocessor import Dispatcher
import argparse
import hashlib
import datetime
import os


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--tool",
        choices=["TL1", "TL31", "TL104", "TL3", "TL4"],
        required=True,
        help="which tool's dataset to register/preprocess/test this run -- "
             "TL1=awdnn, TL31=recheck, TL104=peculiar. Exactly one per "
             "invocation; run again with a different --tool for the others."
    )
    return p.parse_args()


def main():
    cli = parse_args()
    print(f"start main function in temp__code.py  (--tool {cli.tool}) ...............")
    user_id="user"
    dataset_type = "SourceCode"
    username = "baran"
    password = "123"

    # One dataset config per ML tool -- TL1/AWDNN, TL31/ReChecker, TL104/Peculiar.
    # A single run now processes only the ONE selected via --tool, not all
    # three -- see the filtering right after this dict/list below.
    # input_type here is the dataset's storage shape ("folder" or "text"),
    # not to be confused with ML_TOOL_CONFIG's per-tool "-vt" vulnerability
    # type in tool_executor.py (that one is "re" for all three regardless).
    #
    # TL31/ReChecker: dataset_file is usermain.txt, not user.txt -- there is
    # no plain user.txt in train_data/ (only usermain.txt, user.txt.bak,
    # user.txt.bak2, userw.txt). train_data/user is a folder of bare
    # <number>.sol files with no train/valid/test prefix and no label.txt,
    # which tempruntoolwrappertext.py can't read anyway (it expects one
    # manifest file, not a folder) -- usermain.txt is the real, valid,
    # single-file manifest that wrapper actually takes.
    #
    # TL104/Peculiar: dataset_path/dataset_file point at dataset/user, a
    # folder of <split>_<id>.sol files with dataset/label.txt sitting next
    # to it -- this is toolwrapper_tl31_input.py's MODE 2, verified working.
    #
    # TL1/AWDNN: kept at the same path this file already had commented out
    # for it before (tool_path/dataset_path under TL1/AWDNNmain/dataset/).
    # Flagging this honestly: AWDNN's own toolwrapper.py is currently broken
    # independent of this file -- its __main__ block ignores the
    # dataset_path/dataset_file/mode arguments a docker run would pass it,
    # and it has a plain NameError (undefined `tool_result`) on its return
    # path. Registering this dataset will succeed, but an actual run
    # through ToolExecutor for awdnn won't produce real results until that
    # wrapper is fixed separately.
    # bytecode_file/bytecode_input_type default to the legacy xlsx path.
    # xlsx has a hard 32,767-character-per-cell limit that silently
    # truncates (and thereby corrupts) any Bytecode string longer than
    # that -- confirmed on TL31's dataset (28/1000 rows truncated at
    # exactly that length). CSV has no such limit, so once a tool's
    # user_excel.csv has been (re)generated via
    # txt_to_bytecode_excel-for-test1.py, flip its entry here to
    # "user_excel.csv" / "csv". TL31 has been migrated; TL1/TL104/TL3/TL4
    # still need their own user_excel.csv generated before switching.
    tool_dataset_configs = {
        "TL1": {
            "dataset_name": "user",
            "dataset_path": r"/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/",
            "dataset_file": "user.txt",
            "input_type": "text",
            "bytecode_file": "user_excel.xlsx",
            "bytecode_input_type": "excel",
        },
        "TL31": {
            "dataset_name": "user",
            # train_data/user.txt does not exist (only usermain.txt,
            # user.txt.bak, user.txt.bak2, userw.txt live directly under
            # train_data/ -- train_data/user/ is a folder of bare <n>.sol
            # files with no manifest at all). usermain.txt is the real
            # single-file manifest tempruntoolwrappertext.py reads, so
            # dataset_path has to be train_data itself, not train_data/user.
            "dataset_path": r"/mnt/f/LISTTOOL/TL31/ReCheckermaster/train_data",
            "dataset_file": "user.txt",
            "input_type": "text",
            "bytecode_file": "user_excel.csv",
            "bytecode_input_type": "csv",
        },
        "TL104": {
            "dataset_name": "user",
            # dataset/user is a folder of <split>_<id>.sol files + labels.txt --
            # "folder" input_type matched what's on disk for load_dataset()'s
            # own bookkeeping, but ToolExecutor._run_ml_docker() always builds
            # the container path as "/dataset/{dataset_file}", assuming a
            # single manifest file sits directly in dataset_path (that's what
            # the "text" branch + recheck/awdnn's own manifest files satisfy).
            # It has no separate code path for folder-shaped datasets, so
            # dataset_file="user" here resolved to /dataset/user inside the
            # container -- nonexistent, since dataset_path itself (the user/
            # folder) is what got mounted AT /dataset, so there's no nested
            # "user" inside it. Generated dataset/user.txt with
            # FolderdatasetTOtext.generate_txt() (the same helper P3/P4/P8
            # already use) from dataset/user/ + dataset/user/labels.txt, and
            # pointed this config at that manifest instead, matching how
            # TL1/TL31 are registered so ToolExecutor's path-building
            # actually resolves to a real file.
            "dataset_path": r"/mnt/f/LISTTOOL/TL104/peculiar/dataset",
            "dataset_file": "user.txt",
            "input_type": "text",
            "bytecode_file": "user_excel.xlsx",
            "bytecode_input_type": "excel",
        },

        "TL3": {
            "dataset_name": "user",
            "dataset_path": r"/mnt/f/LISTTOOL/TL3/CBGRU/train_data",
            "dataset_file": "user.txt",
            "input_type": "text",
            "bytecode_file": "user_excel.xlsx",
            "bytecode_input_type": "excel",
        },

        "TL4": {
            "dataset_name": "user",
            "dataset_path": r"/mnt/f/LISTTOOL/TL4/WIDENNET/config/train_data",
            "dataset_file": "user.txt",
            "input_type": "text",
            "bytecode_file": "user_excel.xlsx",
            "bytecode_input_type": "excel",
        },

    }

    # only the one dataset config selected via --tool this run -- everything
    # below (registration/preprocessing/test-agent) is untouched, it just
    # now iterates over a list of length 1 instead of 3
    dataset_configs = [tool_dataset_configs[cli.tool]]

    '''
    try:
        user_id = metadataregistrar.login_user(username, password)
        print(f"[INFO] User '{username}' logged in with user_id: {user_id}")
    except ValueError:

        user_id = metadataregistrar.register_user(username, password)
        print(f"[INFO] User '{username}' created with user_id: {user_id}")
    '''

#......................................................................

    metadata_project = metadataregistrar.create_metadata_project(

        user_id=user_id
        )

    metadataregistrar.save_metadata_project(metadata_project)
    print("save metadata_project in Database")
    project_id=metadata_project["project_id"]


#......................................................................
    # register the dataset for the selected tool (--tool)

    registered_datasets = []
    for cfg in dataset_configs:
        base_path = os.path.join(cfg["dataset_path"])

        metadata_dataset = metadataregistrar.create_metadata_dataset(
            dataset_path=base_path,
            project_id=project_id,
            dataset_type=dataset_type,
            dataset_name=cfg["dataset_name"],
            dataset_file=cfg["dataset_file"],
            input_type=cfg["input_type"]
          )

        metadataregistrar.save_metadata_dataset(metadata_dataset)
        print(f"save metadata_dataset in Database ({cfg['dataset_name']})")
        registered_datasets.append(metadata_dataset)

    # kept for downstream code that still refers to a single
    # "metadata_dataset" (e.g. the excel registrations right below) --
    # matches this file's original single-dataset variable
    metadata_dataset = registered_datasets[-1]

#......................................................................

    metadata_dataset_user_excell = metadataregistrar.create_metadata_dataset(dataset_path=os.path.join(dataset_configs[-1]["dataset_path"]),
        project_id=project_id,
        dataset_type="bytecode",
        dataset_name="user_excel",
        dataset_file=dataset_configs[-1]["bytecode_file"],
        input_type=dataset_configs[-1]["bytecode_input_type"]
      )


    metadataregistrar.save_metadata_dataset(metadata_dataset_user_excell)
    print("save metadata_dataset in Database")

#......................................................................
    metadata_dataset_ethereum = metadataregistrar.create_metadata_dataset(dataset_path=r"/mnt/f/LISTTOOL/TL1/AWDNNmain/dataset/ethereum_dataset",
        project_id=project_id,
        dataset_type="bytecode",
        dataset_name="ethereum",
        dataset_file="D2_ethereum.xlsx",
        input_type="excel"
      )


    metadataregistrar.save_metadata_dataset(metadata_dataset_ethereum)
    print("save metadata_dataset in Database")
#......................................................................


#**********************************************************************
    # Each ml-category tool (recheck, awdnn, peculiar) is registered by its
    # own tool_name/tool_path here, same as the static tools below -- this
    # used to be a single hardcoded tool_name="ml" registration pointing at
    # one tool_path (see ToolExecutor's ML_TOOL_CONFIG in tool_executor.py
    # for the matching per-tool image/wrapper/interpreter wiring).
    for tool_name, tool_path in [
            
            #("recheck",   "/mnt/f/LISTTOOL/TL31/ReCheckermaster"),
            #("ml",     "/mnt/f/LISTTOOL/TL1/AWDNNmain"),
            #("ml",   "/mnt/f/LISTTOOL/TL104/peculiar"),
            #("peculiar",  "/mnt/f/LISTTOOL/TL104/peculiar"),
            #("ml", "/mnt/f/LISTTOOL/TL4/WIDENNET"),
            #("ml", "/mnt/f/LISTTOOL/TL3/CBGRU"),
            ("ml",   "/mnt/f/LISTTOOL/TL31/ReCheckermaster"),

            #("ml",     "/mnt/f/LISTTOOL/TL1/AWDNNmain"),
            ("manticore", "/mnt/f/LISTTOOL/Framework/RUN/tools/manticore"),
            ("mythril",   "/mnt/f/LISTTOOL/Framework/RUN/tools/mythril"),
            ("oyente",    "/mnt/f/LISTTOOL/Framework/RUN/tools/oyente"),
            ]:
            metadata_tool= metadataregistrar.create_metadata_tool(
                tool_path=tool_path,
                project_id=project_id,
                tool_name=tool_name,
                input_format="text"
            )
            metadataregistrar.save_metadata_tool(metadata_tool)

#......................................................................

    # preprocess the selected tool's dataset (registered_datasets has
    # exactly one entry now, matching --tool)
    all_preprocessed_ok = True
    for ds in registered_datasets:
        result_data_preprocessor = metadataregistrar.invoke_data_preprocessor(
                                    ds["dataset_path"],
                                    ds["project_id"],
                                    ds["dataset_id"],
                                    ds["dataset_type"])

        if result_data_preprocessor["status"] == "success":
            print(f"GUI: Data Preprocessor finished successfully for {ds['dataset_name']}.")
        else:
            all_preprocessed_ok = False
            print(f": Data Preprocessor failed or returned nothing for {ds['dataset_name']}.(data preprocessor failed)")

    if all_preprocessed_ok:
        result_test_agent = metadataregistrar.invoke_test_agent(
            project_id,
            metadata_dataset["dataset_id"]
        )
        if result_test_agent["status"] == "success":
            print("Test pipeline finished successfully")
        else:
            print("Test pipeline failed or returned nothing.(test_agent failed )")
    else:
        print("Skipping test agent: at least one dataset failed preprocessing.")


    print(f"end main function in temp__code.py  (--tool {cli.tool}) ****************************************************************")

if __name__ == "__main__":

    main()
