
from googleapiclient.discovery import build
import google.auth
from datetime import datetime


credentials, _ = google.auth.default()

# V1 is needed to call all methods except for the ones related to folders
rm_v1_client = build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False) 

# V2 is needed to call folder-related methods
rm_v2_client = build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False) 

ORGANIZATION_ID = '523109014902'
parent="organizations/"+ORGANIZATION_ID

org = rm_v1_client.organizations().get(name=parent).execute()
print(org,end="\n\n")

def project_label_check(project):
    p = rm_v1_client.projects().get(projectId=project['projectId']).execute()
    print(p,end='\n\n')

    print(p['labels'],end='\n\n')

    email_body = "Following label(s) is(are) missing.\n or empty.\n \n\n"
    #service, team, manager, cost, startdate, enddate, environment, type, company
    if 'service' in p['labels']:
        if p['labels']['service'].isspace() or p['labels']['service'] == "":
            email_body += "  - [service] label is empty.\n"
    else:
        email_body += "  - [service] label is missing.\n"

    if 'team' in p['labels']:
        if p['labels']['team'].isspace() or p['labels']['team'] == "":
            email_body += "  - [team] label is empty.\n"
    else:
        email_body += "  - [team] label is missing.\n"

    if 'manager' in p['labels']:
        if p['labels']['manager'].isspace() or p['labels']['manager'] == "":
            email_body += "  - [manager] label is empty.\n"
    else:
        email_body += "  - [manager] label is missing.\n"

    if 'cost' in p['labels']:
        if p['labels']['cost'].isspace() or p['labels']['cost'] == "":
            email_body += "  - [cost] label is empty.\n"
    else:
        email_body += "  - [cost] label is missing.\n"

    if 'environment' in p['labels']:
        if p['labels']['environment'].isspace() or p['labels']['environment'] == "":
            email_body += "  - [environment] label is empty.\n"
    else:
        email_body += "  - [environment] label is missing.\n"

    if 'type' in p['labels']:
        if p['labels']['type'].isspace() or p['labels']['type'] == "":
            email_body += "  - [type] label is empty.\n"
    else:
        email_body += "  - [type] label is missing.\n"

    if 'company' in p['labels']:
        if p['labels']['company'].isspace() or p['labels']['company'] == "":
            email_body += "  - [company] label is empty.\n"
    else:
        email_body += "  - [company] label is missing.\n"

    if 'startdate' in p['labels']:
        if p['labels']['startdate'].isspace() or p['labels']['startdate'] == "":
            email_body += "  - [startdate] label is empty.\n"
    else:
        email_body += "  - [startdate] label is missing.\n"

    if 'enddate' in p['labels']:
        try:
            endtime = datetime.strptime(p['labels']['enddate'], "%Y-%m-%d")            
            if endtime < datetime.now():
                email_body += "  - [enddate] The project is overdue.\n"
        except:
            email_body += "  - [enddate] label is not valid.\n"
    else:
        email_body += "  - [enddate] label is missing.\n"

    print(email_body,end='\n\n')
    return

def folder_check(tree_path, folder):
    tree_path+="-"+folder['displayName']
    print(tree_path,end='\n\n')

    subfolders = rm_v2_client.folders().list(parent=folder['name']).execute()
    print(subfolders,end='\n\n')
    if subfolders:
        for sub in subfolders['folders']:
            folder_check(tree_path, sub)

    folder_ids = [f['name'].split('/')[1] for f in folders_under_org['folders']]
    filter='parent.type="folder" AND parent.id="{}"'.format(folder['name'].split('/')[1])
    print(filter,end='\n\n')
    projects_under_folder = rm_v1_client.projects().list(filter=filter).execute()
    print(projects_under_folder,end='\n\n')
    if projects_under_folder:
        for p in projects_under_folder['projects']:
            #check label
            print(p,end="\n\n")
            project_label_check(p)
            #update organizeation_tree
            project_body={
                'parent':{'type':'folder','id':'{}'.format(p['parent']['id'])},
                'labels':{"organization_tree":'{}'.format(tree_path)}
            }
            print(project_body,end="\n\n")
            rm_v1_client.projects().update(projectId=p['projectId'],body=project_body).execute()


    return


folders_under_org = rm_v2_client.folders().list(parent=parent).execute()
print(folders_under_org, end="\n\n")

for f in folders_under_org['folders']:
    folder_check("root", f)

filter='parent.type="organization" AND parent.id={}'.format(ORGANIZATION_ID)
projects_under_org = rm_v1_client.projects().list(filter=filter).execute()
print(projects_under_org, end="\n\n")

for p in projects_under_org['projects']:
    print(p,end="\n\n")
    project_label_check(p)

    #set organization_tree empty as it's on the root
    
    project_body={
        'parent':{'type':'organization','id':'{}'.format(p['parent']['id'])},
        'labels':{"organization_tree":"root"}
    }
    print(project_body,end="\n\n")
    rm_v1_client.projects().update(projectId=p['projectId'],body=project_body).execute()



def listAllProjects():
    # Start by listing all the projects under the organization
    filter='parent.type="organization" AND parent.id={}'.format(ORGANIZATION_ID)
    projects_under_org = rm_v1_client.projects().list(filter=filter).execute()

    print(projects_under_org)
    # Get all the project IDs
    all_projects = [p['projectId'] for p in projects_under_org['projects']]
    print(all_projects)

    # Now retrieve all the folders under the organization
    parent="organizations/"+ORGANIZATION_ID
    folders_under_org = rm_v2_client.folders().list(parent=parent).execute()

    # Make sure that there are actually folders under the org
    if not folders_under_org:
        return all_projects

    # Now sabe the Folder IDs
    folder_ids = [f['name'].split('/')[1] for f in folders_under_org['folders']]

    # Start iterating over the folders
    while folder_ids:
        # Get the last folder of the list
        current_id = folder_ids.pop()
        
        # Get subfolders and add them to the list of folders
        subfolders = rm_v2_client.folders().list(parent="folders/"+current_id).execute()
        
        if subfolders:
            folder_ids.extend([f['name'].split('/')[1] for f in subfolders['folders']])
        
        # Now, get the projects under that folder
        filter='parent.type="folder" AND parent.id="{}"'.format(current_id)
        projects_under_folder = rm_v1_client.projects().list(filter=filter).execute()
        
        # Add projects if there are any
        if projects_under_folder:
            all_projects.extend([p['projectId'] for p in projects_under_folder['projects']])

    # Finally, return all the projects
    return all_projects

