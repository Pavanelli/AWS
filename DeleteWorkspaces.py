#Crie um arquivo txt workspaces.txt com os ids das workspaces na mesma pasta deste script use o script ListWorkspace para capturar as workspaces não utilizadas.
import boto3

def excluir_workspaces_por_id(ids_workspaces):
    client = boto3.client('workspaces')
    
    for workspace_id in ids_workspaces:
        try:
            response = client.terminate_workspaces(
                TerminateWorkspaceRequests=[
                    {
                        'WorkspaceId': workspace_id
                    }
                ]
            )
            print(f"Workspace {workspace_id} excluída com sucesso.")
        except Exception as e:
            print(f"Erro ao excluir workspace {workspace_id}: {e}")

# Função para ler os IDs das workspaces de um arquivo de texto
def ler_ids_do_arquivo(nome_arquivo):
    with open(nome_arquivo, 'r') as file:
        ids_workspaces = [line.strip() for line in file if line.strip()]
    return ids_workspaces

# Nome do arquivo que contém a lista de IDs das workspaces a serem excluídas
nome_arquivo = 'workspaces.txt'

# Chame a função para ler os IDs das workspaces do arquivo
ids_workspaces = ler_ids_do_arquivo(nome_arquivo)

# Chame a função para excluir as workspaces
excluir_workspaces_por_id(ids_workspaces)
