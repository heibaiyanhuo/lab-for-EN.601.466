## Instructions

### Project structure
- lwp_parser.py, a tool that extracts the non-local images' sources on a given website.
- robot_base.py, a crawler that automatically extracts information on a domain
- helper.py, a script that supports robot_base.py
- content.txt, a text file that contains the phone/email/city information retrieved by the robot
- traversal.log, a log file that contains the traversal information when the robot trapses.

### Environment
Use Python3 and install the required module *BeautifulSoup4*. There is a requirement.txt provided, so you can just run
```sh
pip install -r requirements.txt
```

### How to run the script
#### lwp_parser.py
```sh
python lwp_parser.py https://www.cs.jhu.edu
```
The script will print out the non-local images' sources in https://www.cs.jhu.edu. You can replace it with other urls. But you should ensure the url starts with http or https.

#### robot_base.py
```sh
python robot_base.py https://cs.jhu.edu/\~yarowsky
```
The script will print out all the pdf link when traversing. And it will record the current link into the log file traversal.log. The phone/email/city information will be recorded in the content.txt.