[comment]: # "Auto-generated SOAR connector documentation"
# Cloaken

Publisher: Cypherint  
Connector Version: 1\.0\.0  
Product Vendor: Cypherint  
Product Name: Cloaken  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 4\.2\.7532  

This app implements investigative actions to support Url Unshortener

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Cloaken asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**server\_url** |  required  | string | Server URL
**username** |  required  | string | Username
**password** |  required  | password | Password

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[lookup url](#action-lookup-url) - Check for the presence of a url in a threat intelligence feed  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'lookup url'
Check for the presence of a url in a threat intelligence feed

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**url** |  required  | URL to lookup | string |  `url` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.parameter\.url | string |  `url` 
action\_result\.status | string | 
action\_result\.data\.\*\.unshortened\_url | string |  `url` 
action\_result\.message | string | 
action\_result\.summary | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 