import pandas as pd


def results_to_df(results_dict, *args, **kwargs):

    convert_numeric = kwargs.pop('convert_numeric', True)
    convert_dates = kwargs.pop('convert_dates', 'coerce')
    #df = pd.conca(map(pd.DataFrame.from_dict, results_dict), axis=1)
    df = pd.DataFrame(results_dict)
    #if convert_numeric:
    #    df = df.convert_objects(convert_numeric=convert_numeric, copy=True)
    #if convert_dates:
    #    df = df.convert_objects(convert_dates=convert_dates, copy=True)
    return df

