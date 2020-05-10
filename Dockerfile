FROM python

RUN pip install click munch pyyaml timeago discord

CMD python3 /usr/app/src/WrkzdBot.py


