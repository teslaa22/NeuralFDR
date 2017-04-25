import numpy as np
import matplotlib.pyplot as plt
from matplotlib import mlab

from scipy.stats import beta

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim

from numpy import array
from scipy.cluster.vq import kmeans2


def generate_data_1D(job=0, n_samples=10000,data_vis=0, num_case=4):
    if job == 0: # discrete case
        pi1=np.random.uniform(0,0.3,size=num_case)
        X=np.random.randint(0, num_case, n_samples)
        
        p = np.zeros(n_samples)
        h = np.zeros(n_samples)
        
        for i in range(n_samples):
            rnd = np.random.uniform()
            if rnd > pi1[X[i]]:
                p[i] = np.random.uniform()
                h[i] = 0
            else:
                p[i] = np.random.beta(a = np.random.uniform(0.2,0.4), b = 4)
                h[i] = 1
        return p, h, X

    
    
def generate_data_1D_cont(pi1, X, job=0):
    if job == 0: # discrete case
        n_samples = len(X)
        p = np.zeros(n_samples)
        h = np.zeros(n_samples)
        
        for i in range(n_samples):
            rnd = np.random.uniform()
            if rnd > pi1[i]:
                p[i] = np.random.uniform()
                h[i] = 0
            else:
                p[i] = np.random.beta(a = np.random.uniform(0.2,0.4), b = 4)
                h[i] = 1
        return p, h, X
    
    
def p_value_beta_fit(p, lamb=0.8, bin_num=50, vis=0):
    pi_0=np.divide(np.sum(p>lamb), p.shape[0] * (1-lamb))
    temp_p=np.zeros([0])
    step_size=np.divide(1,np.float(bin_num))
    fil_num=np.int(np.divide(pi_0*p.shape[0],bin_num))+1
    for i in range(bin_num):
        p1=p[p>step_size*(i-1)]
        p1=p1[p1 <= step_size*i]
        choice_num= np.max(p1.shape[0] - fil_num,0)
        if choice_num > 1:
            choice=np.random.choice(p1.shape[0], choice_num)
            temp_p=np.concatenate([temp_p,p1[choice]]).T
    if vis==1:
        plt.figure()
        plt.hist(temp_p, bins=100, normed=True)       
    a, b, loc, scale = beta.fit(temp_p,floc=0,fscale=1)
    return pi_0, a, b
def beta_mixture_pdf(x,pi_0,a,b):
    return beta.pdf(x,a,b)*(1-pi_0)+pi_0

def Storey_BH(x, alpha = 0.05, lamb=0.4):
    pi0_hat=np.divide(np.sum(x>lamb),x.shape[0] *(1-lamb))
    alpha /= pi0_hat
    x_s = sorted(x)
    n = len(x_s)
    ic = 0
    for i in range(n):
        if x_s[i] < i*alpha/float(n):
            ic = i
    return ic, x_s[ic], pi0_hat

def Opt_t_cal_discrete(p, h, X, num_case=2,step_size=0.0001,ub=0.05,n_samples=10000,alpha=0.05):
    # Fit the beta mixture parameters
    fit_param=np.zeros([num_case, 3])
    for i in range(num_case):
        fit_param[i,:]=p_value_beta_fit(p[X==i])

    # Calculating the ratios 
    t_opt=np.zeros([num_case])
    max_idx=np.argmin(fit_param[:,0])
    x_grid = np.arange(0, ub, step_size)
    t_ratio=np.zeros([num_case,x_grid.shape[0]])
    for i in range(num_case):
        t_ratio[i,:] = np.divide(beta_mixture_pdf(
            x_grid,fit_param[i,0],fit_param[i,1],fit_param[i,2]), fit_param[i,0])

    # Increase the threshold
    for i in range(len(x_grid)):
        t=np.zeros([num_case])
        # undate the search optimal threshold
        t[max_idx]=x_grid[i]
        c=t_ratio[max_idx,i]
        for j in range(num_case):
            if j != max_idx: 
                for k in range(len(x_grid)):
                    if k == len(x_grid)-1:
                        t[j]=x_grid[k]
                        break
                    if t_ratio[j,k+1]<c:
                        t[j]=x_grid[k]
                        break
        # calculate the FDR
        num_dis=0 
        num_fd =0 
        for i in range(num_case):
            num_dis+=np.sum(p[X==i] < t[i])
            num_fd+=np.sum(X==i)*t[i]*fit_param[i,0]

        if np.divide(num_fd,np.float(np.amax([num_dis,1])))<alpha:
            t_opt=t
        else:
            break
    return t_opt

def generate_data_2D(job=0, n_samples=10000,data_vis=0):
    if job == 0: # Gaussian mixtures 
        x1 = np.random.uniform(-1,1,size = n_samples)
        x2 = np.random.uniform(-1,1,size = n_samples)
        pi1 = ((mlab.bivariate_normal(x1, x2, 0.25, 0.25, -0.5, -0.2)+
               mlab.bivariate_normal(x1, x2, 0.25, 0.25, 0.7, 0.5))/2).clip(max=1)        
        p = np.zeros(n_samples)
        h = np.zeros(n_samples)
               
        for i in range(n_samples):
            rnd = np.random.uniform()
            if rnd > pi1[i]:
                p[i] = np.random.uniform()
                h[i] = 0
            else:
                p[i] = np.random.beta(a = 0.3, b = 4)
                h[i] = 1
        X = np.concatenate([[x1],[x2]]).T
        
        if data_vis == 1:
            fig = plt.figure()
            ax1 = fig.add_subplot(121)
            x_grid = np.arange(-1, 1, 1/100.0)
            y_grid = np.arange(-1, 1, 1/100.0)
            X_grid, Y_grid = np.meshgrid(x_grid, y_grid)
            pi1_grid = ((mlab.bivariate_normal(X_grid, Y_grid, 0.25, 0.25, -0.5, -0.2)+
               mlab.bivariate_normal(X_grid, Y_grid, 0.25, 0.25, 0.7, 0.5))/2).clip(max=1)  
            ax1.pcolor(X_grid, Y_grid, pi1_grid)
            
            ax2 = fig.add_subplot(122)
            alt=ax2.scatter(x1[h==1][1:50], x2[h==1][1:50],color='r')
            nul=ax2.scatter(x1[h==0][1:50], x2[h==0][1:50],color='b')
            ax2.legend((alt,nul),('50 alternatives', '50 nulls'))
            
        return p, h, X
    if job == 1: # Linear trend
        pass
    if job == 2: # Gaussian mixture + linear trend
        pass
    
def BH(x, alpha = 0.05):
    x_s = sorted(x)
    n = len(x_s)
    ic = 0
    for i in range(n):
        if x_s[i] < i*alpha/float(n):
            ic = i
    return ic, x_s[ic]

def Storey_BH(x, alpha = 0.05, lamb=0.4):
    pi0_hat=np.divide(np.sum(x>lamb),x.shape[0] *(1-lamb))
    alpha /= pi0_hat
    x_s = sorted(x)
    n = len(x_s)
    ic = 0
    for i in range(n):
        if x_s[i] < i*alpha/float(n):
            ic = i
    return ic, x_s[ic], pi0_hat

def p_value_beta_fit(p, lamb=0.8, bin_num=50, vis=0):
    pi_0=np.divide(np.sum(p>lamb), p.shape[0] * (1-lamb))
    temp_p=np.zeros([0])
    step_size=np.divide(1,np.float(bin_num))
    fil_num=np.int(np.divide(pi_0*p.shape[0],bin_num))+1
    for i in range(bin_num):
        p1=p[p>step_size*(i-1)]
        p1=p1[p1 <= step_size*i]
        choice_num= np.max(p1.shape[0] - fil_num,0)
        if choice_num > 1:
            choice=np.random.choice(p1.shape[0], choice_num)
            temp_p=np.concatenate([temp_p,p1[choice]]).T
    if vis==1:
        plt.figure()
        plt.hist(temp_p, bins=100, normed=True)       
    a, b, loc, scale = beta.fit(temp_p,floc=0,fscale=1)
    return pi_0, a, b
def beta_mixture_pdf(x,pi_0,a,b):
    return beta.pdf(x,a,b)*(1-pi_0)+pi_0

def Storey_BH(x, alpha = 0.05, lamb=0.4):
    pi0_hat=np.divide(np.sum(x>lamb),x.shape[0] *(1-lamb))
    alpha /= pi0_hat
    x_s = sorted(x)
    n = len(x_s)
    ic = 0
    for i in range(n):
        if x_s[i] < i*alpha/float(n):
            ic = i
    return ic, x_s[ic], pi0_hat

def Opt_t_cal_discrete(p, h, X, num_case=2,step_size=0.0001,ub=0.05,n_samples=10000,alpha=0.05):
    # Fit the beta mixture parameters
    fit_param=np.zeros([num_case, 3])
    for i in range(num_case):
        fit_param[i,:]=p_value_beta_fit(p[X==i])

    # Calculating the ratios 
    t_opt=np.zeros([num_case])
    max_idx=np.argmin(fit_param[:,0])
    x_grid = np.arange(0, ub, step_size)
    t_ratio=np.zeros([num_case,x_grid.shape[0]])
    for i in range(num_case):
        t_ratio[i,:] = np.divide(beta_mixture_pdf(
            x_grid,fit_param[i,0],fit_param[i,1],fit_param[i,2]), fit_param[i,0])

    # Increase the threshold
    for i in range(len(x_grid)):
        t=np.zeros([num_case])
        # undate the search optimal threshold
        t[max_idx]=x_grid[i]
        c=t_ratio[max_idx,i]
        for j in range(num_case):
            if j != max_idx: 
                for k in range(len(x_grid)):
                    if k == len(x_grid)-1:
                        t[j]=x_grid[k]
                        break
                    if t_ratio[j,k+1]<c:
                        t[j]=x_grid[k]
                        break
        # calculate the FDR
        num_dis=0 
        num_fd =0 
        for i in range(num_case):
            num_dis+=np.sum(p[X==i] < t[i])
            num_fd+=np.sum(X==i)*t[i]*fit_param[i,0]

        if np.divide(num_fd,np.float(np.amax([num_dis,1])))<alpha:
            t_opt=t
        else:
            break
    return t_opt

def result_summary(h,pred):
    print("Num of alternatives:",np.sum(h))
    print("Num of discovery:",np.sum(pred))
    print("Num of true discovery:",np.sum(pred * h))
    print("Actual FDR:", 1-np.sum(pred * h) / np.sum(pred))
    
def softmax_prob_cal(X,Centorid, intensity=1):
    dist=np.zeros([n_samples,num_clusters])
    dist+=np.sum(X*X,axis=1, keepdims=True)
    dist+=np.sum(centroid.T*centroid.T,axis=0, keepdims=True)
    dist -= 2*X.dot(centroid.T)
    dist=np.exp(dist*intensity)
    dist /= np.sum(dist,axis=1, keepdims=True)
    return dist


def get_network(num_layers = 7, node_size = 10, dim = 1):
    
    
    class Model(nn.Module):
        def __init__(self, num_layers, node_size, dim):
            super(Model, self).__init__()
            l = []
            l.append(nn.Linear(dim,node_size))
            l.append(nn.LeakyReLU(0.1))
            for i in range(num_layers - 2):
                l.append(nn.Linear(node_size,node_size))
                l.append(nn.LeakyReLU(0.1))

            l.append(nn.Linear(node_size,1))
            l.append(nn.Sigmoid())

            self.layers = nn.Sequential(*l)



        def forward(self, x):
            x = self.layers(x)
            x = 0.1 * x
            return x

   
    
    
    network = Model(num_layers, node_size, dim)
    return network


def train_network_to_target_p(network, optimizer, x, target_p, num_it = 1000):
    target = Variable(torch.from_numpy(target_p.astype(np.float32)))
    l1loss = nn.L1Loss()
    batch_size = len(x)
    n_samples = len(x)
    loss_hist = []
    

    for iteration in range(num_it):
        if iteration % 100 == 0:
            print iteration
        choice = range(n_samples)
        x_input = Variable(torch.from_numpy(x[choice].astype(np.float32).reshape(batch_size,1)))

        optimizer.zero_grad()
        output = network.forward(x_input) 

        loss = l1loss(output, target)
        loss.backward()

        optimizer.step()
        loss_hist.append(loss.data[0])
    
    return loss_hist

def train_network(network, optimizer, x, p, num_it = 3000, alpha = 0.05):
    
    batch_size = len(x)
    n_samples = len(x)
    loss_hist = []
    soft_compare = nn.Sigmoid()

    for iteration in range(num_it):
        if iteration % 100 == 0:
            print iteration
        choice = range(n_samples)
        x_input = Variable(torch.from_numpy(x[choice].astype(np.float32).reshape(batch_size,1)))
        p_input = Variable(torch.from_numpy(p[choice].astype(np.float32).reshape(batch_size,1)))

        optimizer.zero_grad()
        output = network.forward(x_input) 
        s = torch.sum(soft_compare((output - p_input) * 1e3)) / batch_size #disco rate
        s2 = torch.sum(soft_compare((p_input - (1-output)) * 1e3)) / batch_size #false discoverate rate(over all samples)

        gain = s  - 2 * soft_compare((s2 - s * alpha) * 5e4) 

        loss = -gain
        loss.backward()

        optimizer.step()
        loss_hist.append(loss.data[0])
    
    return loss_hist, s, s2