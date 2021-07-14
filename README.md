# Six Degrees of Youtube
This is the source code for the Six Degrees of Youtube project: https://six-degrees-of-youtube.cookiehook.com

The purpose of this is for you to find more good music on Youtube, based on who your favourite artists like to work with.
For information on how to use this, see the website. This readme explains the logic flow behind the application.

## Algorithm approach
To calculate collaborations, this app will:
1. Search for a Youtube channel matching the name the user typed in.
2. Retrieve all videos uploaded by that channel.
3. Search through the title and description of the video and identifies collaborations through links matching the pattern:
- https://www.youtube.com/watch?v=WEqTS_P3jjM (Link to other video)
- https://www.youtu.be/WEqTS_P3jjM (Compressed link to video)
- https://www.youtube.com/channel/UCo3AxjxePfj6DHn03aiIhww (Link to channel by ID)
- https://www.youtube.com/c/VioletOrlandi (Link to channel by custom URL)
- https://www.youtube.com/VioletOrlandi (Link to channel by custom URL)
- https://www.youtube.com/user/VioletaOrlandi (Link to channel by username)
4. Retrieving uploaded videos by any of the channels linked in any of those videos.
5. Compare descriptions and titles of all videos from all the channels found above to create a map of collaborations.
6. Render a HTML page embedded with the Anychart JS library to render the graph.

The Collaborations panel works by implementing custom click event listeners that look for clicks on any of the lines or
notes of the chart. These extract the data for the channel(s) involved and send another request back to the server for
information about those channels. That is then rendered in an iframe, which is automatically reloaded.

## Deployment
Deployment is managed by Terraform. The application exists as an EC2 running a dockerised application, deployed through
autoscaling group. All VPC and Iam roles that are required are generated by the terraform config. There are only three
pre-reqiuisits for deployment, as seen in the main.tf:
- Route53 domain and SSL certificate
- IAM role that allows Cloudwatch access for RDS monitoring.
- Access tokens associated with a user with permissions to deploy all resources.