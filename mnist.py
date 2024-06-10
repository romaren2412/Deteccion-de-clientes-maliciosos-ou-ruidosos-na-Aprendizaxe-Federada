import datetime
import torch.nn as nn
import os
from arquivos import *
from byzantine import *
from rede import MnistNet
from datos import *
from aggregation import select_aggregation


def adestrar(args, total_clients):
    # Decide el dispositivo de ejecución
    if args.gpu == -1:
        device = torch.device('cpu')
    else:
        device = torch.device('cuda', args.gpu)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join('PROBAS', args.home_path, timestamp, args.aggregation, args.byz_type)
    if not os.path.exists(path):
        os.makedirs(path)

    # Parámetros
    undetected_byz = np.intersect1d([i for i in range(args.nbyz)], total_clients)
    undetected_byz_index = np.where(np.isin(total_clients, undetected_byz))[0]
    lr = args.lr
    epochs = args.nepochs
    train_acc_list = []
    softmax_cross_entropy = nn.CrossEntropyLoss()

    ########################################################################################################
    # EJECUCIÓN
    with device:
        num_outputs = 10

        # ARQUITECTURA DO MODELO
        net = MnistNet(num_channels=1, num_outputs=num_outputs)
        net.initialize_weights()
        net.to(device)

        ########################################################################################################
        # CARGA DO DATASET
        train_data_loader, test_data_loader, test_data = preparar_datos()
        each_worker_data, each_worker_label = repartir_datos(args, train_data_loader, len(total_clients), device)

        # ATAQUE DIRIXIDO
        target = 0
        each_worker_data, each_worker_label = backdoor(each_worker_data, each_worker_label, undetected_byz, target)

        ####################################################################################################
        # TIPO DE ATAQUE
        byz = select_byzantine_range(args.byz_type)

        ####################################################################################################

        for e in range(epochs):
            grad_list = []
            for i in range(len(total_clients)):
                inputs, labels = each_worker_data[i][:], each_worker_label[i][:]
                # NON ACUMULAR GRADIENTES
                net.zero_grad()
                outputs = net(inputs)
                loss = softmax_cross_entropy(outputs, labels)
                loss.backward()
                grad_list.append([param.grad.clone() for param in net.parameters()])
            param_list = [torch.cat([xx.view(-1, 1) for xx in x], dim=0) for x in grad_list]

            # ATACAR
            param_list = byz(param_list, undetected_byz_index)

            # SELECCIONAR MÉTODO DE AGREGACIÓN
            select_aggregation(args.aggregation, param_list, net, lr, undetected_byz_index)

            #############################################################################
            # PRECISIÓNS
            # CALCULAR A PRECISIÓN DO ENTRENO CADA 10 ITERACIÓNS
            if (e + 1) % 5 == 0:
                testear_precisions(test_data_loader, net, device, e, train_acc_list, path, target, args.byz_type)

    # CALCULAR A PRECISIÓN FINAL DO TESTEO
    resumo_final(test_data_loader, net, device, e)

    return None
