# Bhadra

Bhadra is a vulnerability management tool. It allows you to manage your application security, maintaining various products, helps to triage vulnerabilities and push findings to defect trackers.

It is designed to improve the security posture within Razorpay and effectively helps program management on below areas
  - how our deployment can be aligned with production
  - how SAST, SCA, container scanning can be aligned with deployment
  - how repo level mapping helps to track the findings and 
  - how different tools can be configured at different engagement.

## Quick Start



```sh
git clone https://github.com/razorpay/bhadra
cd bhadra
# building
docker-compose build
# running
docker-compose up
# obtain admin credentials. the initializer can take up to 3 minutes to run
# use docker-compose logs -f initializer to track progress
docker-compose logs initializer | grep "Admin password:"
```

## Adding new tools/parser
To add new tools refer this [parser](dojo/tools)

## Reflecting tool results on frontend
To reflect the tools on frontend - Add the tool name to this variable "VISIBLE_TOOLS_NAME" on this [Settings](dojo/settings/settings.dist.py) file 

## Simple and easy

- Kept the UI very simple by showing needed information to security folks and developer.
- Designed for Appsec folks to give holistic view about different tools results in one place for a specific product
- Bhadra Flow
  <img width="1210" alt="bhadra-flow" src="https://github.com/razorpay/bhadra/assets/98045500/372a35fb-96b6-4252-a57b-3ce29ee820df">

  Products are considered as github repo, Engagements are considered as tools (semgrep, dependabot,..), daily scans will create a Tests.

- Goal is to keep things as simple about the finding and it should be developer friendly. Target audience of the tools is not 
limited to Security folks. And we changed the UI/UX to keep it simple and neat.
- Dashboard shows the findings by tool level along with Product types and product count. Tool level vulnerabilities redirect it to active findings
- Product Type View shows the findings by tool level along with overall active findings. Product view shows all the open findings.
- Configure the variable "VISIBLE_TOOLS_NAME" on this file [Settings](dojo/settings/settings.dist.py) file in order to show what tools should dashboard shows.

## Our success stories

- All our deployments are in fully cloud native fashion and the velocity of deployment is also high.
- Different tooling for SAST, SCA, DAST, Container Scanning, CSPM, etc., and also some custom tools. Security anlayst/developer hop to different tools to verify and fix vulnerabilities.
- Github repo act as a source and all toolings are intergrated in one or other way.
- Want to build a single glass of pane for all the vulnerabilities. In that way, service owner knows the security posture of their components.
- Bhadra solves that problem by keep on pushing all the results on daily basis from different tools and always provided the Point-In-Time data.
  - All github repo points to any one of Business Unit.
  - Engagement and tools are always 1:1 ratio. That is, engagement is nothing but the tool which we are integrating for the repo/product. E.g bhadra_Semgrep_Scan, bhadra_Dependabot_Scan.
  - Automation will pull the data from different sources and create a test. So daily tests are getting created for each engagement for each product.
- Bhadra shows the near real data which can be consumed to find a score card for the services or pull the data to visualize results in BI tools like Looker, Superset, etc.
## Kubernetes deployment

All the application specifc and secrets are passed as k8s config. Postgresql used as a k8s statefulset. See [k8s files](k8s)



