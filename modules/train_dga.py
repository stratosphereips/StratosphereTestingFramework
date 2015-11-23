# Part of this file was taken from Viper - https://github.com/botherder/viper
# The rest is from the Stratosphere Testing Framework
# See the file 'LICENSE' for copying permission.

# Example file of how to create a module without persistence in the database. Useful for obtaining statistics or processing data.

from stf.common.out import *
from stf.common.abstracts import Module
from stf.core.models import  __groupofgroupofmodels__ 
from stf.core.dataset import __datasets__
from stf.core.notes import __notes__
from stf.core.connections import  __group_of_group_of_connections__
from stf.core.models_constructors import __modelsconstructors__ 
from stf.core.labels import __group_of_labels__
from modules.markov_models_1 import __group_of_markov_models__
from modules.distances_1 import __group_of_distances__
from itertools import compress
import random

group_normal=[2248,2249,2250,2252,2253,2254,2255,2256,2257]
group_malware_nodga=[2260,2261,2264,2267,2273,2281,2282,2284,2283]
group_malware1_dga=[2263,2266,2268,2269,2270,2271,2274,2265] 
group_malware2_dga=[2236,2238,2240,2239,2241,2242,2243,2244] 
group_fastflux=[2279,2280,2278]

test=[2251,2262,2272,2237,2235]

allgroups=[]
allgroups.extend(group_normal)
allgroups.extend(group_malware_nodga)
allgroups.extend(group_malware1_dga)
allgroups.extend(group_malware2_dga)
allgroups.extend(group_fastflux)

def parse_final_metrics( results_str):
        final_results={}
        (confusion_matrix,metrics)=results_str.split(',')
        final_results['ErrorRate']=float(metrics.split()[0].split(':')[1])
        final_results['PLR']=float(metrics.split()[1].split(':')[1])
        final_results['FNR']=float(metrics.split()[2].split(':')[1])
        final_results['TNR']=float(metrics.split()[3].split(':')[1])
        final_results['Precision']=float(metrics.split()[4].split(':')[1])
        final_results['PPV']=float(metrics.split()[5].split(':')[1])
        final_results['FDR']=float(metrics.split()[6].split(':')[1])
        final_results['TPR']=float(metrics.split()[7].split(':')[1])
        final_results['FMeasure1']=float(metrics.split()[8].split(':')[1])
        final_results['FPR']=float(metrics.split()[9].split(':')[1])
        final_results['DOR']=float(metrics.split()[10].split(':')[1])
        final_results['NLR']=float(metrics.split()[11].split(':')[1])
        final_results['NPV']=float(metrics.split()[12].split(':')[1])
        final_results['Accuracy']=float(metrics.split()[13].split(':')[1])
        
        final_results['TN']=float(confusion_matrix.split()[0].split(':')[1])
        final_results['FP']=float(confusion_matrix.split()[1].split(':')[1])
        final_results['FN']=float(confusion_matrix.split()[2].split(':')[1])
        final_results['TP']=float(confusion_matrix.split()[3].split(':')[1])
        
        return final_results


class ExperimentDGA(Module):
    cmd = 'experimentdga'
    description = 'Example module to print some statistics about the data in stf'
    authors = ['harpo']

    def __init__(self):
        # Call to our super init
        super(ExperimentDGA, self).__init__()
        self.parser.add_argument('-t', '--train', action='store_true', help='train')
        self.parser.add_argument('-T', '--test', action='store_true', help='test')

    def test(self):
        fd=open("/home/harpo/dga_test_results.dat",'w')

        for model in allgroups:
            metrics_dict={}
            testset_str=','.join(str(i) for i in test)
            final_errors_metrics=__group_of_distances__.create_new_distance(100,model,testset_str,0)
            print >>fd,model
            print >>fd,final_errors_metrics
            print >>fd,threshold
            print >>fd
            fd.flush()

        fd.close()



    def train(self):
        fd=open("/home/harpo/dga_train_results.dat",'w')

        for model in allgroups:
                
                metrics_dict={}
                g1i=random.randint(0,len(group_normal)-1)
                g2i=random.randint(0,len(group_malware_nodga)-1)
                g3i=random.randint(0,len(group_malware1_dga)-1)
                g4i=random.randint(0,len(group_malware2_dga)-1)
                g5i=random.randint(0,len(group_fastflux)-1)

                print "model :",model
                for x in range(0,10):
                    print "lap:",x

                    if model == group_normal[g1i]:
                        g1i=(g1i+1)%len(group_normal)
                    elif model == group_normal[g2i]:
                        g2i=(g2i+1)%len(group_malware_nodga)
                    elif model == group_normal[g3i]:
                        g3i=(g3i+1)%len(group_malware1_dga)
                    elif model == group_normal[g4i]:
                        g4i=(g4i+1)%len(group_malware2_dga)
                    elif model == group_normal[g5i]:
                        g5i=(g5i+1)%len(group_fastflux)

                    valset=[group_normal[g1i],
                            group_malware_nodga[g2i],
                            group_malware1_dga[g3i],
                            group_malware2_dga[g4i],
                            group_fastflux[g5i]]
                   
                    mask=[1]*len(allgroups)
                    trained=allgroups.index(model)
                    mask[trained]=0
                    mask[allgroups.index(group_normal[g1i])]=0
                    mask[allgroups.index(group_malware_nodga[g2i])]=0
                    mask[allgroups.index(group_malware1_dga[g3i])]=0
                    mask[allgroups.index(group_malware2_dga[g4i])]=0
                    mask[allgroups.index(group_fastflux[g5i])]=0
                    trainset=list(compress(allgroups,mask))

                    g1i=(g1i+1)%len(group_normal)
                    g2i=(g2i+1)%len(group_malware_nodga)
                    g3i=(g3i+1)%len(group_malware1_dga)
                    g4i=(g4i+1)%len(group_malware2_dga)
                    g5i=(g5i+1)%len(group_fastflux)

                    trainset_str=','.join(str(i) for i in trainset)
                    valset_str=','.join(str(i) for i in valset)
                    __group_of_markov_models__.run()
                    threshold=__group_of_markov_models__.train(model,"",trainset_str,0)

                    final_errors_metrics=parse_final_metrics(__group_of_distances__.create_new_distance(100,model,valset_str,0))
                    final_errors_metrics['threshold']=float(threshold)
                    metrics_dict[x]=final_errors_metrics

                  #  print >>fd,model
                  #  print >>fd,final_errors_metrics
                  #  print >>fd,threshold
                  #  print >>fd
                  #  fd.flush()
                    
                sorted_metrics = sorted(metrics_dict.items(), key=lambda x: (x[1]['FMeasure1'], -x[1]['FPR'], x[1]['TPR'], x[1]['PPV'], x[1]['NPV'], x[1]['TP'], x[1]['TN'], -x[1]['FP'], -x[1]['FN'], x[1]['Precision'], -x[0]), reverse=True)
                print "####################"
                for metric in sorted_metrics:
                    print  metric
                print "####################"
                avg_threshold=sum([sorted_metrics[i][1]['threshold']  for i in range(0,10)])/10.0
                print "avg threshold :",avg_threshold

                if _threshold != -1:
                    final_threshold=avg_threshold
                elif model in group_normal and avg_threshold ==-1:
                    final_threshold=2.0 
                elif model not in group_normal and avg_threshold ==-1:
                    final_threshold=1.1
                __group_of_markov_models__.get_markov_model(model).set_threshold(final_threshold)

                print >>fd,"*"*50
                print >>fd,"id:",model
                print >>fd,"avgt:",avg_threshold
                print >>fd,"finalt:",final_threshold
                for metric in sorted_metrics:
                    print>>fd,  metric
                fd.flush()
        fd.close()
                    


    def run(self):
        # List general info
        def help():
            self.log('train', "train module for DGA")

        # Run?
        super(ExperimentDGA, self).run()
        if self.args is None:
            return

        if self.args.train:
            self.train()
       
        if self.args.test:
            self.test()
        else:
            print_error('At least one of the parameter is required')
            self.usage()
