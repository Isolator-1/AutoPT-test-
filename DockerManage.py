import docker, yaml, os, subprocess

def parse_yml(app, CVE):
    with open(os.path.join('./vulhub-master', app, CVE, 'docker-compose.yml')) as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
        image_name = result['services'][app]['image']
    return image_name

def get_container_by_images(image_name):
    client = docker.from_env()
    containers = client.containers.list()
    matching_containers = []
    for container in containers:
        if container.image.tags and image_name in container.image.tags:
            matching_containers.append(container)
    return matching_containers[0]

def get_container_ip(container):
    ip = container.exec_run("hostname -i").output
    return ip.decode('ascii').rstrip('\n')

def docker_compose_up_build(app, CVE):
    yml_path = os.path.join('./vulhub-master', app, CVE)
    if os.path.exists(yml_path):
        # retval = os.getcwd()
        # os.chdir(yml_path)
        # os.system('docker-compose up -d')
        # os.chdir(retval)
        command = ['docker-compose', 'up', '-d']
        p = subprocess.Popen(command, cwd = yml_path)
        p.wait()
    else:
        raise Exception(" invalid app & CVE in `docker_compose_up_build` ")

def destroy_container(app, CVE):
    yml_path = os.path.join('./vulhub-master', app, CVE)
    if os.path.exists(yml_path):
        command = ['docker-compose', 'down', '-v']
        p = subprocess.Popen(command, cwd = yml_path)
        p.wait()
    else:
        raise Exception(" invalid app & CVE in `docker_compose_up_build` ")

def rm_images(image_name):
    client = docker.from_env()
    image = client.images.get(image_name)
    image.remove()


if __name__== '__main__':
    # image_name = parse_yml('php','CVE-2012-1823')
    # print(image_name)

    # docker_compose_up_build('php', 'CVE-2012-1823')
    # x = get_container_by_images('vulhub/php:5.4.1-cgi')
    # ip = get_container_ip(x)
    # print(ip)

    # attack

    # destroy_container('php', 'CVE-2012-1823')
    # rm_images('vulhub/php:5.4.1-cgi')
    
    pass