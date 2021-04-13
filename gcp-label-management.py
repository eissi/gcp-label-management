
from googleapiclient.discovery import build
import google.auth
from datetime import datetime
from datetime import timedelta 
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


alert_mail_to_env = os.environ.get('ALERT_EMAIL_TO')
alert_mail_to = alert_mail_to_env.split(',')
print(alert_mail_to,end='\n\n')

alert_mail_from = os.environ.get('ALERT_EMAIL_FROM')

credentials, _ = google.auth.default()

# V1 is needed to call all methods except for the ones related to folders
rm_v1_client = build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False) 

# V2 is needed to call folder-related methods
rm_v2_client = build('cloudresourcemanager', 'v2', credentials=credentials, cache_discovery=False) 

# rm_v1_client.projects().getancestry()
ORGANIZATION_ID = os.environ.get("ORGANIZATION_ID")
parent="organizations/"+ORGANIZATION_ID

sendgrid_key = os.environ.get('SENDGRID_API_KEY')

folder_to_manage = os.environ.get('FOLDER_TO_MANAGE').lower()
#folder_to_manage = 'root-{}'.format(folder_to_manage)
print('folder_to_manage: {}'.format(folder_to_manage),end='\n\n')

# org = rm_v1_client.organizations().get(name=parent).execute()
# print(org,end="\n\n")

def sendmail(subject, body):
    print('subject: {}'.format(subject))
    print('body: {}'.format(body))
    message = Mail(
        from_email=alert_mail_from,
        to_emails=alert_mail_to,
        subject=subject,
        html_content=format(body))
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def project_label_check(p):
    #print(p['labels'],end='\n\n')

    default_body="<p>Following label(s) is(are) missing. or empty. \n\n</p>"
    email_body = default_body

    #service, team, manager, cost, startdate, enddate, environment, type, company
    if 'labels' in p:
        if 'service' in p['labels']:
            if p['labels']['service'].isspace() or p['labels']['service'] == "":
                email_body += "<p>  - [service] label is empty.\n</p>"
        else:
            email_body += "<p>  - [service] label is missing.\n</p>"

        if 'team' in p['labels']:
            if p['labels']['team'].isspace() or p['labels']['team'] == "":
                email_body += "<p>  - [team] label is empty.\n</p>"
        else:
            email_body += "<p>  - [team] label is missing.\n</p>"

        if 'manager' in p['labels']:
            if p['labels']['manager'].isspace() or p['labels']['manager'] == "":
                email_body += "<p>  - [manager] label is empty.\n</p>"
        else:
            email_body += "<p>  - [manager] label is missing.\n</p>"

        if 'cost' in p['labels']:
            if p['labels']['cost'].isspace() or p['labels']['cost'] == "":
                email_body += "<p>  - [cost] label is empty.\n</p>"
        else:
            email_body += "<p>  - [cost] label is missing.\n</p>"

        # if 'environment' in p['labels']:
        #     if p['labels']['environment'].isspace() or p['labels']['environment'] == "":
        #         email_body += "<p>  - [environment] label is empty.\n</p>"
        # else:
        #     email_body += "<p>  - [environment] label is missing.\n</p>"

        # if 'type' in p['labels']:
        #     if p['labels']['type'].isspace() or p['labels']['type'] == "":
        #         email_body += "<p>  - [type] label is empty.\n</p>"
        # else:
        #     email_body += "<p>  - [type] label is missing.\n</p>"

        # if 'company' in p['labels']:
        #     if p['labels']['company'].isspace() or p['labels']['company'] == "":
        #         email_body += "<p>  - [company] label is empty.\n</p>"
        # else:
        #     email_body += "<p>  - [company] label is missing.\n</p>"

        if 'startdate' in p['labels']:
            if p['labels']['startdate'].isspace() or p['labels']['startdate'] == "":
                email_body += "<p>  - [startdate] label is empty.\n</p>"
        else:
            email_body += "<p>  - [startdate] label is missing.\n</p>"

        if 'enddate' in p['labels']:
            try:
                endtime = datetime.strptime(p['labels']['enddate'], "%Y-%m-%d")   
                print(endtime)
                print(datetime.now()+timedelta(days=7),end='\n\n')        
                print(endtime<datetime.now())
                print(endtime<datetime.now()+ timedelta(days=7))
                print(endtime<datetime.now()+ timedelta(days=30)) 

                if endtime < datetime.now():
                    print('[Warning] Google Project ID, {}, has passed the end date.'.format(p['projectId']),end='\n\n')
                    sendmail('[Warning] Google Project ID, {}, has passed the end date.'.format(p['projectId']),"none")
                    #email_body += "<p>  - [enddate] The project is overdue.\n</p>"
                elif (endtime < datetime.now() + timedelta(days=7)):
                    print('[Info] Google Project ID, {}, will pass the end date next week!.'.format(p['projectId']),end='\n\n')
                    sendmail('[Info] Google Project ID, {}, will pass the end date next week!.'.format(p['projectId']),"none")
                elif (endtime < datetime.now() + timedelta(days=30)):
                    print('[Info] Google Project ID, {}, will pass the end date next month.'.format(p['projectId']),end='\n\n')
                    sendmail('[Info] Google Project ID, {}, will pass the end date next month.'.format(p['projectId']),"none")
                    
            except:
                email_body += "<p>  - [enddate] label is not valid.\n</p>"
        else:
            email_body += "<p>  - [enddate] label is missing.\n</p>"
    else:
        email_body += "<p>  - ALL LABELS ARE MISSING.\n</p>"

    print(email_body,end='\n\n')

    if email_body != default_body:
        #print("temp")
        sendmail('[Warning] Google Project ID, {}, has violated the labeling policy'.format(p['projectId']), email_body)

    return

def folder_check(tree_path, folder):
    tree_path+="-"+folder['displayName'].lower().replace('-','_')
    print(tree_path,end='\n\n')



    subfolders = rm_v2_client.folders().list(parent=folder['name']).execute()
    print(subfolders,end='\n\n')
    if subfolders:
        for sub in subfolders['folders']:
            folder_check(tree_path, sub)

    if tree_path.find(folder_to_manage) != 0:
        return

    print("entering to manage projects under organization")
    #folder_ids = [f['name'].split('/')[1] for f in folders_under_org['folders']]
    filter='parent.type="folder" AND parent.id="{}" AND lifecycleState="ACTIVE"'.format(folder['name'].split('/')[1])
    print(filter,end='\n\n')

    projects_under_folder = rm_v1_client.projects().list(filter=filter).execute()
    if 'nextPageToken' in projects_under_folder:   
        # pageToken = projects_under_org['nextPageToken']
        print(projects_under_folder['nextPageToken'],end='\n\n')
        print("Page tokenization should be implemented")
        raise Exception("Sorry, page tokenization should be implemented")
    print(projects_under_folder,end='\n\n')
    if projects_under_folder:
        for p in projects_under_folder['projects']:
            #check label
            print(p,end="\n\n")
            project = rm_v1_client.projects().get(projectId=p['projectId']).execute()
            print(project,end='\n\n')
            project_label_check(project)
            #update organizeation_tree
            # if 'organization_tree' in project['labels']:
            if 'labels' in project:
                project['labels']['organization_tree'] = tree_path
            else:
                project['labels']={'organization_tree': tree_path}

            #project[labels] += {"organization_tree":'{}'.format(tree_path)} 
            # project_body={
            #     'parent':{'type':'folder','id':'{}'.format(p['parent']['id'])},
            #     'labels':{"organization_tree":'{}'.format(tree_path)}
            # }
            print(project,end="\n\n")
            rm_v1_client.projects().update(projectId=p['projectId'],body=project).execute()


    return

def project_labeling_management(request):
    folders_under_org = rm_v2_client.folders().list(parent=parent).execute()
    print(folders_under_org, end="\n\n")

    for f in folders_under_org['folders']:
        folder_check("root", f)

    filter='parent.type="organization" AND parent.id={} AND lifecycleState="ACTIVE"'.format(ORGANIZATION_ID)

    if folder_to_manage == "root":
            # pageToken=""
            # while True:
        projects_under_org = rm_v1_client.projects().list(filter=filter).execute()
        print(projects_under_org,end='\n\n')
            # projects_under_org = rm_v1_client.projects().list(filter=filter, pageSize=1, pageToken=projects_under_org['nextPageToken']).execute()
            # print(projects_under_org,end='\n\n')
            # projects_under_org = rm_v1_client.projects().list(filter=filter, pageSize=2, pageToken=projects_under_org['nextPageToken']).execute()
            # print(projects_under_org,end='\n\n')
        if 'nextPageToken' in projects_under_org:
            # pageToken = projects_under_org['nextPageToken']
            print(projects_under_org['nextPageToken'],end='\n\n')
            print("Page tokenization should be implemented")
            raise Exception("Sorry, page tokenization should be implemented")

        # print(projects_under_org, end="\n\n")

        for p in projects_under_org['projects']:
            print(p,end="\n\n")
            project_label_check(p)

            #set organization_tree empty as it's on the root
            project = rm_v1_client.projects().get(projectId=p['projectId']).execute()
            print(project,end='\n\n')
            if 'labels' in project:
                project['labels']['organization_tree'] = 'root'
            else:
                project['labels']={'organization_tree': 'root'}
            print(project,end='\n\n')
            rm_v1_client.projects().update(projectId=p['projectId'],body=project).execute()

                # if pageToken == "":
                #     break

    return "Success"

if __name__ == "__main__":
    project_labeling_management("")