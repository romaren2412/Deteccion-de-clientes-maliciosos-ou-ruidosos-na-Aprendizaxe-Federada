import torch


def evaluate_accuracy(data_loader, model, device):
    model.eval()  # Cambiar el modo del modelo a evaluación
    correct = 0
    total = 0

    with torch.no_grad():
        for data, label in data_loader:
            data, label = data.to(device).float(), label.to(device).float()
            output = model(data)
            _, predicted = torch.max(output.data, 1)
            total += label.size(0)
            correct += (predicted == label).sum().item()

    accuracy = correct / total
    return accuracy


def evaluate_accuracy_un_batch(data_loader, model, device):
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        data, label = data_loader
        data, label = data.to(device).float(), label.to(device).float()
        output = model(data)
        _, predicted = torch.max(output.data, 1)
        total += label.size(0)
        correct += (predicted == label).sum().item()

    accuracy = correct / total
    return accuracy


def evaluate_backdoor(data_iterator, net, target, device):
    net.eval()
    correct_predictions = 0
    total_samples = 0

    with torch.no_grad():
        for i, (data, label) in enumerate(data_iterator):
            data, label = data.to(device), label.to(device)
            data[:, :, 26, 26] = 1
            data[:, :, 26, 24] = 1
            data[:, :, 25, 25] = 1
            data[:, :, 24, 26] = 1

            # Inicializa la lista de índices
            remaining_idx = list(range(data.shape[0]))

            # Se evalúa la precisión del ataque en los ejemplos que inicialmente NO eran de la clase destino.
            # "Elimina" los ejemplos que SÍ son de la clase de destino
            # Establece las etiquetas de los ejemplos que NO son de la clase de destino a la clase de destino
            # (objetivo del ataque)
            for example_id in range(data.shape[0]):
                if label[example_id] == target:
                    remaining_idx.remove(example_id)
                else:
                    label[example_id] = target

            # Propagación hacia adelante
            output = net(data)

            # Obtén las predicciones
            _, predictions = torch.max(output, 1)
            predictions = predictions[remaining_idx]
            label = label[remaining_idx]

            # Actualiza el conteo de predicciones correctas
            correct_predictions += (predictions == label).sum().item()
            total_samples += len(remaining_idx)

    accuracy = correct_predictions / total_samples
    return accuracy
