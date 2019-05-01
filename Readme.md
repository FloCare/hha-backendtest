
### Summary:
This is part of the Flocare project and is the backend service for managing the home health care agencies. This backend
service provides APIs for creating and modifying the entities managed by this system.

#### Other services:
1. Mobile App (android/ios repo) - #TODO fill github repo here
2. Web Dashboard (js Admin dashboard to interact with this backend service) - #TODO fill github repo here


#### Entity Definition:
The major entities are listed and defined below. For the complete list of entities browse in models.py for the 
different modules (phi/models.py, user_auth/models.py and flocarebase/models.py)
#####Patient:
The patient that the office and clinicians track. Created by admin from the dashboard
 (Refer to `Other services` heading). Can be assigned to clinicians of this home health.  

##### Clinicians:
The main users of the mobile app. They have a list of patients that they need to take care of and create visits for
 their patients. The clinicians have multiple roles (RN - Registered nurse, PT - Physical Therapist, etc. For the
 complete list of roles refer to `phi/management/commands/utils/constants.py:48`)

##### Care Team:
A patient can be taken care of by multiple clinicians. All these clinicians form the care team for this patient.


##### Places:
There is a list of places that can be created through the admin dashboard. These are common to all the clinicians in
 their home health and will be synced to their mobile apps. They could include places like a lab or hospital that their
 clinicians might go to. 

##### Visit:
Clinicians create visits for the patients/place for a particular date that they need to visit the patient on. They can set
 the time of the visit and for patient visits this information is synced to all members of the careteam.
 
A visit may also have mileage information associated with it. This mileage information is sent from the app to the
 backend service).  


##### Physician:
A physician is a doctor/surgeon in the hospitals. Uniquely identified by their NPI id, they are created from the
 admin dashboard. A patient can have a physician assigned to them.

##### Report:
Clinicians may create a report according to the cycle followed in their homehealth(15 days - 30 days). This report will
 have the visit information and the mileage information for each of the visit. The total miles for the report is also
 shown to know the total miles for which the clinician needs to be reimbursed. 
 
 The create-report API also has some validations to verify that the expected miles is same for both the client and the
 backend. If this does not match, the API returns an error and the client is responsible for updating the visit
 information with new miles before calling this API again. 


### **`Installation and Usage instructions`**

#### Prerequisites:
Install postgresql

On mac, `brew install postgresql`

#### Install and setup virtualenv:

1. pip3 install virtualenv
2. virtualenv env
3. To activate the environment, source env/bin/activate.

#### Install requirements:
In the enivornment, run the following command.

`pip install -r requirements.txt`


If you get a installation error with `psycopg2`, use the following command instead.

`pip install -r requirements.txt --global-option=build_ext --global-option="-I/usr/local/opt/openssl/include" --global-option="-L/usr/local/opt/openssl/lib"`


#### Starting the server locally:
Activate the environment - `source env/bin/activate`

Change the db credentials in `backend/settings/dev.py`. Update the name, user and password to the local db credentials.
 
Run the server with `python manage.py runserver`

To run the migrations - `python manage.py migrate`

#### Deploying the server on cloud:

To deploy this server you need to add the secret key in `backend/settings/prod.py`. Uncomment the **SECRET_KEY** key
 in the file and replace it with the environment variable.