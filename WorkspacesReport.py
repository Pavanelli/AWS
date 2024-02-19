# report for AWS Workspace Usage
import boto3
from datetime import date, datetime

# const
THRESHOLD_DAYS = 15

# running counts
running_count = 0
non_used_count = 0
threshold_count = 0

# Nome do arquivo para salvar os resultados
output_file = 'workspace_report.txt'

def run_it(message):

    # Abrir o arquivo de saída para escrita
    with open(output_file, 'w') as f:
        # Escrever a mensagem de início e a data no arquivo
        f.write(f'{message}\n')
        f.write(f'Report Date: {datetime.now()}\n\n')

        print(f'{message}')
        aws = boto3.session.Session()
        client = aws.client('workspaces')

        response = client.describe_workspaces()
        workspaces = response['Workspaces']
        print_workspace(client, workspaces, f)
        while "NextToken" in response:
            response = client.describe_workspaces(NextToken=response["NextToken"])
            workspaces = response['Workspaces']
            print_workspace(client, workspaces, f)
        print('')
        f.write('\n')
        f.write(f'Total Workspaces: {running_count}\n')
        f.write(f'Never Been Used Count: {non_used_count}\n')
        f.write(f'Past threshold Count: {threshold_count} haven\'t been used in the last {THRESHOLD_DAYS} days\n')


def print_workspace(client, workspaces, f):
    workspaceIds = [workspace['WorkspaceId'] for workspace in workspaces]
    response = client.describe_workspaces_connection_status(WorkspaceIds=workspaceIds)
    statuses = response['WorkspacesConnectionStatus']
    for status in statuses:
        workspaceId = status["WorkspaceId"]
        user_name = get_user_for_workspace(workspaceId, workspaces)

        if "LastKnownUserConnectionTimestamp" not in status:
            # no known usage, so they've never used it
            print_usage(-1, workspaceId, user_name, f)

        else:
            tmp = status['LastKnownUserConnectionTimestamp']
            last_used_date = tmp.replace(tzinfo=None)
            today = datetime.now()
            delta = today - last_used_date
            print_usage(delta.days, workspaceId, user_name, f)


def print_usage(days, workspace_id, user, f):
    print(f'{days}, {workspace_id} ,{user}')

    global running_count
    global non_used_count
    global threshold_count
    global THRESHOLD_DAYS
    running_count += 1

    # Escrever as informações no arquivo
    f.write(f'{days}, {workspace_id} ,{user}\n')

    if days < 0:
        non_used_count += 1
    if days > THRESHOLD_DAYS:
        threshold_count += 1


def get_user_for_workspace(workspace_id, workspaces):
    for workspace in workspaces:
        if workspace["WorkspaceId"] == workspace_id:
            return workspace["UserName"]

    return ""



if __name__ == '__main__':
    run_it('AWS Workspace Report')
