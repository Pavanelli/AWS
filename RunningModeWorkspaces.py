import boto3

# Criar um cliente para o serviço WorkSpaces
workspaces_client = boto3.client('workspaces')

# Lista para armazenar todos os WorkSpaces
all_workspaces = []

# Paginar para obter todos os WorkSpaces
paginator = workspaces_client.get_paginator('describe_workspaces')
for page in paginator.paginate():
    all_workspaces.extend(page['Workspaces'])

# Iterar sobre cada WorkSpace e modificar as propriedades
for workspace in all_workspaces:
    workspace_id = workspace['WorkspaceId']
    print("Modificando as propriedades do WorkSpace:", workspace_id)
    try:
        workspaces_client.modify_workspace_properties(WorkspaceId=workspace_id, WorkspaceProperties={'RunningMode': 'AUTO_STOP'})
    except Exception as e:
        print(f"Erro ao modificar as propriedades do WorkSpace {workspace_id}: {str(e)}")

print("Modo de execução foi configurado para auto stop em todos os WorkSpaces.")