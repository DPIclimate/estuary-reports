FROM ubuntu:22.10
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
    #&& rm -rf /var/lib/apt/lists/*

# Set timezone:
ENV TZ=Australia/Sydney
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install tzdata dependency after setting timezone to ensure CLI prompts don't prevent image build.
RUN apt-get update && apt-get install -y tzdata

RUN apt-get --assume-no install -y \
    texlive-full

COPY requirements.txt .

RUN pip3 install -r requirements.txt

RUN rm requirements.txt