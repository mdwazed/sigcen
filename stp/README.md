Production deployment ready repo of sigcen automation app.\
Creates 3 docker container. Django and uwsgi resides in one container,Nginx resides in another container and mysql in third container.\
Nginx <-> uWsgi <-> Django <->mysql\
see docker-compose file for the config arangements and expossed port.\

Django development server could be used during development.\

Fol steps need to be carried out for priduction deployment:\
    
    - Clone the repo\
    - login django container bash and create super user
    - copy local settings to the location where settings.py file resides.\