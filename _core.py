import numpy as np
from algorithms import *
from tools import *

__all__ = ['model_selection',
           'minimal_model', 'nested_lists']
   
def model_selection(data, labels, test_data, test_labels,
                    mu_range, tau_range, lambda_range,
                    cv_splits, error_function, 
                    data_normalizer=None, labels_normalizer=None,
                    returns_kcv_errors=False):
    """Short Summary.
    
    Extended Summary.
    
    Parameters
    ----------
    name1 :  array_like
        Description of `name1`
    name2 :  file or str, optional (the default is 'foo')
        Description of `name2`
    name3 : {1, 2, 3}
        Description of `name3`
    
    Returns
    -------
    name :  type
        description
        
    Notes
    -----
    Eventually notes and LaTeX [1]_ formulae
    
    .. math::
    
        \sum_{i=1}^N = 1
        
    References
    ----------
    .. [1] "Guide to LaTEX", foo editions

    Examples
    --------
    >>> np.add(1, 2)
    3
    
    Second example
    
    >>> np.add([1, 2], [3, 4])
    array([4, 6])
    
    """
    
    stage1_out = minimal_model(data, labels, mu_range[0],
                               tau_range, lambda_range,
                               cv_splits, error_function,
                               data_normalizer, labels_normalizer,
                               returns_kcv_errors)
    tau_opt, lambda_opt = stage1_out[0:2]
    
    stage2_out = nested_lists(data, labels,
                              test_data, test_labels,
                              tau_opt, lambda_opt, mu_range,
                              error_function,
                              data_normalizer, labels_normalizer)
    
    return stage1_out + stage2_out

def minimal_model(data, labels, mu, tau_range, lambda_range,
                  cv_splits, error_function,
                  data_normalizer=None, labels_normalizer=None,
                  returns_kcv_errors=False):
    """ TODO: add docstring """
    
    err_ts = list()
    err_tr = list()
    max_tau_num = len(tau_range)
    
    for train_idxs, test_idxs in cv_splits:        
        # First create a view and then normalize (eventually)
        data_tr, data_ts = data[train_idxs,:], data[test_idxs,:]
        if not data_normalizer is None:
            data_tr, data_ts = data_normalizer(data_tr, data_ts)
            
        labels_tr, labels_ts = labels[train_idxs,:], labels[test_idxs,:]
        if not labels_normalizer is None:
            labels_tr, labels_ts = labels_normalizer(labels_tr, labels_ts)
            
        # Builds a classifier for each value of tau
        beta_casc = elastic_net_regpath(data_tr, labels_tr, mu,
                                        tau_range[:max_tau_num])
        
        if len(beta_casc) < max_tau_num: max_tau_num = len(beta_casc)
        _err_ts = np.empty((len(beta_casc), len(lambda_range)))
        _err_tr = np.empty_like(_err_ts)
        
        # For each sparse model builds a
        # rls classifier for each value of lambda
        for j, b in enumerate(beta_casc):
            selected = (b.flat != 0)
            for k, lam in enumerate(lambda_range):
                beta = ridge_regression(data_tr[:,selected], labels_tr, lam)
                
                prediction = np.dot(data_ts[:,selected], beta)
                _err_ts[j, k] = error_function(labels_ts, prediction)
    
                prediction = np.dot(data_tr[:,selected], beta)
                _err_tr[j, k] = error_function(labels_tr, prediction)
        
        err_ts.append(_err_ts)
        err_tr.append(_err_tr)
    
    # cut columns and computes the mean
    err_ts = np.asarray([a[:max_tau_num] for a in err_ts]).mean(axis=0)
    err_tr = np.asarray([a[:max_tau_num] for a in err_tr]).mean(axis=0)

    tau_opt_idx, lambda_opt_idx = np.where(err_ts == err_ts.min())
    tau_opt = tau_range[tau_opt_idx[0]]             # ?? [0] or [-1]
    lambda_opt = lambda_range[lambda_opt_idx[0]]
    
    if returns_kcv_errors:
        return tau_opt, lambda_opt, err_ts, err_tr
    else:
        return tau_opt, lambda_opt

def nested_lists(data, labels, test_data, test_labels,
                 tau, lambda_, mu_range, error_function=None,
                 data_normalizer=None, labels_normalizer=None):
    """ TODO: add docstring """
    
    if not data_normalizer is None:
        data, test_data = data_normalizer(data, test_data)
            
    if not labels_normalizer is None:
        labels, test_labels = labels_normalizer(labels, test_labels)  
    
    beta_list = list()
    selected_list = list()
    if error_function:
        err_tr_list = list()
        err_ts_list = list()
    
    for mu in mu_range:        
        beta = elastic_net(data, labels, mu, tau)
        selected = (beta.flat != 0)
    
        beta = ridge_regression(data[:,selected], labels, lambda_)
           
        if error_function:    
            prediction = np.dot(data[:,selected], beta)
            err_tr_list.append(error_function(labels, prediction))
            
            prediction = np.dot(test_data[:,selected], beta)
            err_ts_list.append(error_function(test_labels, prediction))

        beta_list.append(beta)
        selected_list.append(selected)
                      
    if error_function:
        return beta_list, selected_list, err_tr_list, err_ts_list
    else:
        return beta_list, selected_list
