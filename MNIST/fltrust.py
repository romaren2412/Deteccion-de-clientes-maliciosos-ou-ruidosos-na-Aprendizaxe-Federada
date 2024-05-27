import datetime
import os

import numpy as np
import torch.nn as nn
import torch.utils.data

from MNIST.arquivos import *
from MNIST.datos import repartir_datos, preparar_datos, crear_root_dataset
from MNIST.methods import inicializar_global_model, create_local_models, create_server_model
from aggregation import equal_update, update_model_with_weighted_gradients
from calculos_FLTrust import *


def fltrust(c, total_clients, byz_workers):
    """
    Detecta ataques mediante clustering.
    :param c: obxecto de configuración
    :param total_clients: lista cos clientes totais (a partir do segundo adestramento, os supostamente benignos)
    :param byz_workers: lista cos clientes byzantinos
    :return:
    """
    # Decide el dispositivo de ejecución
    if c.gpu == -1:
        device = torch.device('cpu')
    else:
        device = torch.device('cuda', c.gpu)

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join('MNIST/PROBAS/', c.home_path, timestamp, c.byz_type)
    if not os.path.exists(path):
        os.makedirs(path)

    # EJECUCIÓN
    with device:
        ########################################################################################################
        # CARGA DO DATASET
        train_data, test_data = preparar_datos()
        global_test_data_loader = torch.utils.data.DataLoader(test_data, batch_size=500, shuffle=False)
        worker_loaders = repartir_datos(c, train_data, len(total_clients))

        # DATASET AUXILIAR
        root_dataloader = crear_root_dataset(c, train_data)
        ####################################################################################################

        # ARQUITECTURA DO MODELO - CNN
        global_net = inicializar_global_model(1, 10, device)
        server_model = create_server_model(c, root_dataloader)
        aprendedores = create_local_models(len(total_clients), c, worker_loaders, test_data, byz_workers, global_net)

        ####################################################################################################

        # set upt parameters
        ben_workers = [i for i in total_clients if i not in byz_workers]
        print("CLIENTES BENIGNOS: ", ben_workers)
        print("CLIENTES BYZANTINOS: ", byz_workers)
        print("----------------------------------")

        precision_array = []
        local_precisions = []
        trust_scores_array = []

        grad_list = []

        ###################################################################################################

        # EXECUTAR ATAQUES
        target_backdoor_dba = 7
        if c.byz_type == 'dba':
            for index, g in enumerate(np.array_split(byz_workers, 4)):
                for byzantine in g:
                    aprendedores[byzantine].dba_index = index

        # ##################################################################################################################
        print("COMEZO DO ADESTRAMENTO...")
        # CADA ÉPOCA
        for e in range(c.EPOCH):
            client_updates = []
            local_precisions_ep = []
            local_epoch = 0

            while local_epoch < c.FL_FREQ:
                local_epoch += 1
                # ADESTRAMENTO DE CADA CLIENTE
                for i, ap in enumerate(aprendedores):
                    update = ap.sl.adestrar(nn.CrossEntropyLoss(), global_net, c.byz_type, target_backdoor_dba)
                    if local_epoch == c.FL_FREQ:
                        client_updates.append(update)
                        acc = ap.sl.test(ap.net, ap.testloader)
                        print(f"[Epoca {e}] Cliente: ", str(i), " - Accuracy: ", {acc})
                        local_precisions_ep.append(acc)

                # ADESTRAMENTO DO SERVIDOR
                server_model_update = server_model.sl.adestrar_server(nn.CrossEntropyLoss(), global_net)

            # ACTUALIZAR MODELO GLOBAL
            trust_scores, norm_updates = compute_trust_scores_and_normalize(client_updates, server_model_update)
            trust_scores_array.append(trust_scores)

            # Federar
            if c.aggregation == 'fedavg':
                equal_update(global_net, client_updates, c.LR)
            else:
                update_model_with_weighted_gradients(global_net, norm_updates, trust_scores, c.LR)

            # Gardar resultados
            gardar_puntuacions(trust_scores_array, path, byz_workers)
            local_precisions.append(local_precisions_ep)
            gardar_precisions_locais(path, local_precisions, byz_workers)

            #############################################################################
            # PRECISIÓNS
            # CALCULAR A PRECISIÓN DO ENTRENO CADA 20 ITERACIÓNS
            if (e + 1) % 2 == 0:
                testear_precisions(global_test_data_loader, global_net, device, e, precision_array, path,
                                   target_backdoor_dba, c.byz_type)

        resumo_final(global_test_data_loader, global_net, device)