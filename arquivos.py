import csv

from evaluate import *


def gardar_precisions(path, precision_array, byz_type):
    with open(path + '/acc.csv', 'w', newline='') as csvFile:
        csvwriter = csv.writer(csvFile)
        if byz_type == 'backdoor':
            csvwriter.writerow(["Iteracions", "ACC_Global", "ASR"])
        else:
            csvwriter.writerow(["Iteracions", "ACC_Global"])
        csvwriter.writerows(precision_array)


def testear_precisions(testloader_global, global_net, device, e, precision_array, path, target, byz_type):
    acc_global = evaluate_accuracy(testloader_global, global_net, device)
    if byz_type in ('backdoor', 'dba', 'backdoor_sen_pixel'):
        backdoor_sr = evaluate_backdoor(testloader_global, global_net, target=target, device=device)
        print("Epoch %02d. Train_acc %0.4f Attack_sr %0.4f" % (e, acc_global, backdoor_sr))
        precision_array.append([e, acc_global, backdoor_sr])
    else:
        print("Epoch %02d. Train_acc %0.4f" % (e, acc_global))
        precision_array.append([e, acc_global])
    gardar_precisions(path, precision_array, byz_type)


def resumo_final(test_data_loader, net, device, e):
    test_accuracy = evaluate_accuracy(test_data_loader, net, device)
    print("Epoch %02d. Test_acc %0.4f" % (e, test_accuracy))
