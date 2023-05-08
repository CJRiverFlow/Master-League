# Master League

## Overview

This application is an API for registering match results in a seasonal league. 

The technologies used are AWS Lambda, DynamoDB, Flask, and the Serverless Framework with Serverless plugins.  

The application follows the single table design for DynamoDB.

## Deployment

You should have configured your AWS account and complete the serverless framework setup.

- Clone the repository and run `npm install` to install serverless plugins.

- Run on terminal the following command: `sls deploy --stage dev`.

## Application and Documentation

The API includes endpoints to create teams, new seasons, after registering the teams on a season we can add the match results.

The following points have been implemented:

1. Only matches with teams registered in the season can be created.
2. Teams will only face each other once per season.
3. Matches can only be created for valid seasons and teams.
4. The champion per season should be updated manualy, the route PUT `/api/seasons/{season_id}` can be used for this purpouse.
5. When deleting a season the matches will not be deleted in cascade.
6. There is no match point registration, as the champion is not automatically calculated.

The API documentation is at `/postman` folder but also is available here: https://documenter.getpostman.com/view/17275974/2s93eYUCJ5  
Change the enviroment variable `host` and copy the AWS API Gateway URL recently created.

## Notes

- This application currently focuses exclusively on the implementation of the league results API logic. However, it does not yet include the extra steps for user authentication and authorization besides resources IAM role.
- Pending tests with moto.
