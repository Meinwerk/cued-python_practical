#########################################################
# CUED Python Statistical Spoken Dialogue System Software
#########################################################
#
# Copyright 2015-16  Cambridge University Engineering Department 
# Dialogue Systems Group
#
# Principal Authors:  Dongho Kim and David Vandyke, Pei-Hao (Eddy) Su
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################

import os
import sys

""" DETAILS:
# THIS FILE EXPLORES MCC/GP MODELS
"""

def config_text( domains, root,
                 screen_level,
                 maxturns,
                 bcm,
                 belieftype, useconfreq, policytype, startwithhello, inpolicyfile, outpolicyfile, learning_policy,
                 gamma, nu, epsilon_start, epsilon_end, maxIter, 
                 kernel, thetafile,
                 random, learning, scale,
                 usenewgoalscenarios,
                 nbestsize,
                 patience,
                 penaliseallturns,
                 wrongvenuepenalty,
                 notmentionedvaluepenalty):


    text = '[DEFAULT]'  + '\n'
    text += 'domains = ' + domains + '\n'
    text += 'root = '   + root + '\n'
    text += '\n'

    text += '[logging]' + '\n'
    text += 'screen_level = '   + screen_level + '\n'
    text += '\n'

    text += '[simulate]' + '\n'
    text += 'maxturns = '   + maxturns + '\n'
    text += '\n'

    text += '[policy]'   + '\n'
    text += 'bcm = '    + bcm + '\n'
    text += '\n'
    
    text += '[policy_TT]' + '\n'
    text += 'belieftype = '     + belieftype + '\n'
    text += 'useconfreq = '     + useconfreq + '\n'
    text += 'policytype = '     + policytype + '\n'
    text += 'startwithhello = ' + startwithhello + '\n'
    text += 'inpolicyfile = '   + inpolicyfile + '\n'
    text += 'outpolicyfile = '  + outpolicyfile + '\n'
    text += 'learning = '       + learning_policy + '\n'
    text += '\n'

    text += '[mccpolicy_TT]' + '\n'
    text += 'gamma = '  + gamma + '\n'
    text += 'nu = '  + nu + '\n'
    text += 'epsilon_start = '  + epsilon_start + '\n'
    text += 'epsilon_end = '  + epsilon_end + '\n'
    text += 'maxIter = '  + maxIter + '\n'
    text += '\n'

    text += '[gppolicy_TT]' + '\n'
    text += 'kernel = '  + kernel + '\n'
    text += 'thetafile = '  + thetafile + '\n'
    text += '\n'

    text += '[gpsarsa_TT]' + '\n'
    text += 'random = '  + random + '\n'
    text += 'learning = '  + learning + '\n'
    text += 'scale = '  + scale + '\n'
    text += '\n'

    text += '[um]' + '\n'
    text += 'usenewgoalscenarios = '  + usenewgoalscenarios + '\n'
    text += '\n'

    text += '[em]' + '\n'
    text += 'nbestsize = '  + nbestsize + '\n'
    text += '\n'

    text += '[goalgenerator]' + '\n'
    text += 'patience = '  + patience + '\n'
    text += '\n'

    text += '[eval]' + '\n'
    text += 'penaliseallturns = '  + penaliseallturns + '\n'
    text += 'wrongvenuepenalty = '  + wrongvenuepenalty + '\n'
    text += 'notmentionedvaluepenalty = '  + notmentionedvaluepenalty + '\n'
    text += '\n'

    return text

def run_on_grid(targetDir, execDir, configName, text):

    ################################################
    ### config file
    ################################################
    #config = '/home/dial/phs26/MPhil_practical/gridSearch_script_test/configures/' + configName + '.cfg'
    config = '/home/fl350/cued-python_practical/config/' + configName + '.cfg'
    # if directory not exist, then creat one
    #config_dir = '/home/dial/phs26/MPhil_practical/gridSearch_script_test/configures/'
    config_dir = '/home/fl350/cued-python_practical/config/'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    with open(config, 'w') as f:
        f.write(text)
    
    #python run_grid_pyGPtraining_rpg.py TT_ff 10 1000 3 /home/dial/phs26/system/python/cued-python_rpg_ff/ 15 1 /home/dial/phs26/system/python/cued-python_rpg/config/runAll/configs/simulate-ff.cfg

    runStr = 'running ' + config
    print '{0:*^60}'.format(runStr);

    command = 'python run_grid_training.py ' + targetDir + ' 10 100 1 ' + execDir + ' 15 1 ' + config
    os.system(command)


def main():

	################################################
	###  Domain information
	################################################
        domains          = 'TT'
        #root            = '/home/dial/phs26/MPhil_practical/cued-python_practical/'
        root            = '/home/fl350/cued-python_practical/'
        screen_level    = 'info'
        maxturns        = '30'

	################################################
	###  General policy information
	################################################
        bcm             = 'False' 
        belieftype      = 'focus' 
        useconfreq      = 'False'
        policytype_vary = ['gp']
        startwithhello  = 'True'
        inpolicyfile    = 'policyFile'
        outpolicyfile   = 'policyFile'
        learning        = 'True'

	################################################
	###  MCC policy training options
	################################################
        gamma               = '1.0'
        nu_vary             = ['0.01']
        epsilon_pair        = [('1.0', '0.1')]#, ('1.0','0.5')]
        maxIter             = '2000'

	################################################
	###  GP policy training options
	################################################
        #kernel = 'polysort'                 # 'gausssort'
        #theta = 'thetaFile/linearKernel'    # 'thetaFile/gaussKernel'

        #kernel_theta_pair = [('polysort',root+'thetaFile/linearKernel'), ('gausssort',root+'thetaFile/gaussKernel')]
        # kernel_theta_pair = [
        #         ('gausssort',root+'thetaFile/gaussKernel-p-{0}-l-{1}'.format(p, l))
        #         for p in range(1,6)
        #         for l in range(2,4)]
        kernel_theta_pair = [('polysort',root+'thetaFile/linearKernel')] + \
                [('gausssort',root+'thetaFile/gaussKernel-p-{0}-l-{1}'.format(p, l))
                    for p in range(2,5)
                    for l in range(2,4)]
        kernel_theta_pair *=  5 # 5 trials



        random = 'False'
        learning = 'True'
        scale = '3'

	################################################
	###  User model and environment model info.
	################################################
        usenewgoalscenarios = 'True'
        nbestsize = '3'
        patience = '3'
        penaliseallturns = 'True'
        wrongvenuepenalty = '0'
        notmentionedvaluepenalty = '0'

        
        ConfigCounter = 0
        
        listFile = open(sys.argv[1],'w')
        listOutput = '{0: <6}'.format('PARAM') + '\t'
        listOutput += '{0: <15}'.format('type') + '\t'
        listOutput += '{0: <15}'.format('nu') + '\t'
        listOutput += '{0: <15}'.format('epsilon_start') + '\t'
        listOutput += '{0: <15}'.format('epsilon_end') + '\t'
        listOutput += '{0: <15}'.format('GP kernel') + '\t'

        
        listFile.write(listOutput+'\n')

        execDir = root

        for policytype in policytype_vary:
            if policytype == 'mcc':
                for nu in nu_vary:
                    for epsilon_start, epsilon_end in epsilon_pair:
                        targetDir = 'TT_mcc'
                        kernel = 'XXX'
                        thetafile = 'XXX'
     
                        listOutput = '{0: <15}'.format(policytype) + '\t'
                        listOutput += '{0: <15}'.format(nu) + '\t'
                        listOutput += '{0: <15}'.format(epsilon_start) + '\t'
                        listOutput += '{0: <15}'.format(epsilon_end) + '\t'
                        listOutput += '{0: <15}'.format(kernel) + '\t'

                        targetDir += 'nu_' + nu + '_epsilon_start_' + epsilon_start + '_epsilon_end_' + epsilon_end + ' kernel ' + kernel

			currentPath = os.getcwd()
			currentPath = currentPath.replace('/export/home/mlsalt-helpers/','/home/')
                        configName = targetDir

                        tmpName = 'gRun'+str(ConfigCounter)
                        text = config_text( domains, root,
                                         screen_level,
                                         maxturns,
                                         bcm,
                                     	 belieftype, useconfreq, policytype, startwithhello, 
				     	 currentPath+'/'+tmpName+'/'+inpolicyfile, currentPath+'/'+tmpName+'/'+outpolicyfile, learning,
                                         gamma, nu, epsilon_start, epsilon_end, maxIter, 
                                         kernel, thetafile,
                                         random, learning, scale,
                                         usenewgoalscenarios,
                                         nbestsize,
                                         patience,
                                         penaliseallturns,
                                         wrongvenuepenalty,
                                         notmentionedvaluepenalty)


                        #run_on_grid(targetDir, execDir, configName, text)
                        run_on_grid(tmpName, execDir, tmpName, text)
                        
                        listFile.write(tmpName + '\t' + listOutput+'\n')
                        ConfigCounter += 1



            elif policytype == 'gp':
                for kernel, thetafile in kernel_theta_pair:
                    targetDir = 'TT_gp'
                    nu = 'XXX'
                    epsilon_start = 'XXX'
                    epsilon_end = 'XXX'
                                
                    listOutput = '{0: <15}'.format(policytype) + '\t'
                    listOutput += '{0: <15}'.format(nu) + '\t'
                    listOutput += '{0: <15}'.format(epsilon_start) + '\t'
                    listOutput += '{0: <15}'.format(epsilon_end) + '\t'
                    listOutput += '{0: <15}'.format(kernel) + '\t'

                    targetDir += 'nu_' + nu + '_epsilon_start_' + epsilon_start + '_epsilon_end_' + epsilon_end + ' kernel ' + kernel

		    currentPath = os.getcwd()
		    currentPath = currentPath.replace('/export/home/mlsalt-helpers/','/home/')
                    configName = targetDir

                    tmpName = 'gRun'+str(ConfigCounter)
                    text = config_text( domains, root,
                                     screen_level,
                                     maxturns,
                                     bcm,
                                     belieftype, useconfreq, policytype, startwithhello, 
				     currentPath+'/'+tmpName+'/'+inpolicyfile, currentPath+'/'+tmpName+'/'+outpolicyfile, learning,
                                     gamma, nu, epsilon_start, epsilon_end, maxIter, 
                                     kernel, thetafile,
                                     random, learning, scale,
                                     usenewgoalscenarios,
                                     nbestsize,
                                     patience,
                                     penaliseallturns,
                                     wrongvenuepenalty,
                                     notmentionedvaluepenalty)


                    #run_on_grid(targetDir, execDir, configName, text)
                    run_on_grid(tmpName, execDir, tmpName, text)
                    
                    listFile.write(tmpName + '\t' + listOutput+'\n')
                    ConfigCounter += 1

if __name__ == "__main__":
    main()
# END OF FILE 

