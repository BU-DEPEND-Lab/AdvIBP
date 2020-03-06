import os
import json
import glob
import copy
import importlib
import torch
from IBP_Adv_Training.utils.datasets import loaders


def get_file_close(filename, ext, load=True):
    """
    Helper function to find a file with closest match
    """
    if ext[0] == ".":
        ext = ext[1:]
    if not load:
        return filename + "." + ext
    filelist = glob.glob(filename + "*." + ext + "*")
    if len(filelist) == 0:
        raise OSError("File " + filename + " not found")
    # FIXME
    if "last" in filelist[0]:
        filelist = filelist[1:]
    if len(filelist) > 1:
        filelist = sorted(filelist, key=len)
        print("Warning! Multiple files matches ID {}: {}".format(
            filename, filelist
        ))
        for f in filelist:
            # return the best model if we have it
            if "best" in f:
                return f
    return filelist[0]


def update_dict(d, u, show_warning=False):
    for k, v in u.items():
        if k not in d and show_warning:
            print("\033[91m Warning: key {} not found in config."
                  "Make sure to double check spelling and config option name."
                  "\033[0m".format(k))
        if isinstance(v, dict):
            d[k] = update_dict(d.get(k, {}), v, show_warning)
        else:
            d[k] = v
    return d


def load_config(args):
    print("loading config file: {}".format(args.config))
    with open("config/defaults.json") as f:
        config = json.load(f)
    with open("config/" + args.config) as f:
        update_dict(config, json.load(f))
    if args.overrides_dict:
        print("overriding parameters: "
              "\033[93mPlease check these parameters carefully.\033[0m")
        print("\033[93m" + str(args.overrides_dict) + "\033[0m")
        update_dict(config, args.overrides_dict, True)
    subset_models = []
    # remove ignored models
    for model_config in config["models"]:
        if "ignore" in model_config and model_config["ignore"]:
            continue
        else:
            subset_models.append(model_config)
    config["models"] = subset_models
    # repeat models if the "repeated" field is found
    repeated_models = []
    for model_config in config["models"]:
        if "repeats" in model_config:
            for i in range(model_config["repeats"]):
                c = copy.deepcopy(model_config)
                c["repeats_idx"] = i + 1
                for k, v in c.items():
                    if isinstance(v, str):
                        if v == "##":
                            c[k] = i + 1
                        if "@@" in v:
                            c[k] = c[k].replace("@@", str(i + 1))
                repeated_models.append(c)
        else:
            repeated_models.append(model_config)
    config["models"] = repeated_models
    # only use a subset of models, if specified
    if args.model_subset:
        subset_models = []
        for i in args.model_subset:
            subset_models.append(config["models"][i])
        config["models"] = subset_models
    if args.path_prefix:
        config["path_prefix"] = args.path_prefix
    return config


def config_dataloader(config, **kwargs):
    """
    Load dataset loader based on config file
    """
    return loaders[config["dataset"]](**kwargs)


def get_path(config, model_id, path_name, **kwargs):
    """
    Unified naming rule for model files, bound files,
    ensemble weights and others.
    To change format of saved model names, etc, only change here
    """
    if path_name == "model":
        model_file = get_file_close(
            os.path.join(
                config["path_prefix"], config["models_path"], model_id
            ), "pth", **kwargs
        )
        os.makedirs(
            os.path.join(config["path_prefix"], config["models_path"]),
            exist_ok=True
        )
        return model_file
    if path_name == "best_model":
        model_file = os.path.join(
            config["path_prefix"], config["models_path"],
            model_id + "_best.pth"
        )
        os.makedirs(
            os.path.join(config["path_prefix"], config["models_path"]),
            exist_ok=True
        )
        return model_file
    if path_name == "train_log":
        model_file = get_path(config, model_id, "model", load=False)
        os.makedirs(
            os.path.join(config["path_prefix"], config["models_path"]),
            exist_ok=True
        )
        return model_file.replace(".pth", ".log")
    if path_name == "eval_log":
        model_file = get_path(config, model_id, "model", load=False)
        os.makedirs(
            os.path.join(config["path_prefix"], config["models_path"]),
            exist_ok=True
        )
        return model_file.replace(".pth", "_test.log")
    else:
        raise RuntimeError("Unsupported path " + path_name)


def get_model_config(config, model_id):
    """
    Return config of a single model
    """
    for model_config in config["models"]:
        if model_config["model_id"] == model_id:
            return model_config


def config_modelloader(config, load_pretrain=False, cuda=False):
    """
    Load all models based on config file
    """
    # load the required modelfile
    model_module = importlib.import_module(
        "models." + os.path.splitext(config["network_model"])[0]
    )
    models = []
    model_names = []
    for model_config in config["models"]:
        if "ignore" in model_config and model_config["ignore"]:
            continue
        model_id = model_config["model_id"]
        model_names.append(model_id)
        model_class = getattr(model_module, model_config["model_class"])
        model_params = model_config["model_params"]
        m = model_class(**model_params)
        if cuda:
            m.cuda()
        if load_pretrain:
            model_file = get_path(config, model_id, "model")
            print("Loading model file", model_file)
            checkpoint = torch.load(model_file)
            if isinstance(checkpoint["state_dict"], list):
                checkpoint["state_dict"] = checkpoint["state_dict"][0]
            new_state_dict = {}
            for k in checkpoint["state_dict"].keys():
                if "prev" in k:
                    pass
                else:
                    new_state_dict[k] = checkpoint["state_dict"][k]
            checkpoint["state_dict"] = new_state_dict

            m.load_state_dict(checkpoint["state_dict"])

        models.append(m)
    return models, model_names
