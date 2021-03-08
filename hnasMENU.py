#!/usr/bin/python
# coding=utf-8

# Company: T-Systems do Brasil
# Team: Storage Team
# Author: Gustavo Gidzinski Gomes
# DateOfCreation: 26/02/2021
# LastEdited: In Build...
# Version: 1.0
# Purpose: Script to manage HNAS Storage via API

import csv
import subprocess
import enum
import requests
import json
import os
import urllib.parse
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

BASE_URL = "https://{}:8444/v7/storage/"
HNCL01 = "1.128.51.228"
HNCL02 = "1.128.51.237"
HNCLBKP = "1.128.51.4"
APIKEY1 = 'mnZ2YeoGwr.iaLEExifBfHLWVMHSbIou8HdcQkFPEGicBVNM0z8gzB'
APIKEY2 = 'S07FgtoDTM.TjYixsKGR25Mokiw3.hJQdOCYj2a4bZsGMpTj88FkG3'
APIKEY3 = 'BJaAX8ZdtD.JRm.zOSERmLS9hrdGJdz5zHVt/wFEQL1UObQm2O5xw2'


def getfssnap(storage, apikey, sigla):

    def imprimeErro(storage, sigla):
        mensagem = print('Não existem filesystems com a sigla ' + sigla + ' no Storage ' + storage)
        return mensagem

    payload = {}
    headers = {
        'X-Api-Key': apikey
    }
    urlgetfs = BASE_URL.format(urllib.parse.quote(storage))
    urlgetfs += "filesystems"
    response = requests.request("GET", urlgetfs, headers=headers, data=payload, verify=False)
    fslist = response.json()
    j = json.loads(response.text)
    data = json.dumps(j)
    # fsidlist = []

    if sigla in data:
        output = open('/root/HNASAPI/SnapReports/SnapReport_' + sigla + '.txt', "a")
        for item in fslist['filesystems']:
            fsname = item['label']
            if sigla in str(fsname):
                fsid = item['filesystemId']
                urlgetsnap = BASE_URL.format(urllib.parse.quote(storage))
                urlgetsnap += "filesystem-snapshots/" + fsid + "/null"
                reply = requests.request("GET", urlgetsnap, headers=headers, data=payload, verify=False)
                snaplist = reply.json()
                if len(snaplist) == 1 and snaplist['snapshots']:
                    print("Showing snapshots for volume: " + fsname + '\n', file=output)
                    for snapshot in snaplist['snapshots']:
                        print("Snapshot Name: " + snapshot['displayName'], file=output)
                        print("Created By: " + snapshot['creationReason'], file=output)
                        print("Snapshot Status: " + snapshot['state'] + "\n", file=output)
                else:
                    print("No snaps for volume: " + fsname + '\n', file=output)
                    continue
            else:
                continue
    else:
        imprimeErro(storage, sigla)
        exit(1)
    print("SnapReport Gerado, valide seu e-mail")
    subprocess.call('mail -s "HNAS Snapshot Report" -a ""/root/HNASAPI/SnapReports/SnapReport_' + sigla + '.txt"" '
                    '-r "root@stsprobe01" < "/root/HNASAPI/tmp/message2" '
                    "TS_BRA_STO_SUPPORT@t-systems.com", shell=True)

def getBillingQuota(storage, apikey, sigla):

    def imprimeErro(storage, sigla):
        mensagem = print('Não existem filesystems com a sigla ' + sigla + ' no Storage ' + storage)
        return mensagem

    class SIZE_UNIT(enum.Enum):
        BYTES = 1
        KB = 2
        MB = 3
        GB = 4

    def convert_unit(size_in_bytes, unit):
        """ Convert the size from bytes to other units like KB, MB or GB"""
        if unit == SIZE_UNIT.KB:
            return size_in_bytes//1024
        elif unit == SIZE_UNIT.MB:
            return size_in_bytes//(1024*1024)
        elif unit == SIZE_UNIT.GB:
            return size_in_bytes//(1024*1024*1024)
        else:
            return size_in_bytes

    payload = {}
    headers = {
        'X-Api-Key': apikey
    }
    urlgetfs = BASE_URL.format(urllib.parse.quote(storage))
    urlgetfs += 'filesystems'
    response = requests.request("GET", urlgetfs, headers=headers, data=payload, verify=False)
    fslist = response.json()
    j = json.loads(response.text)
    data = json.dumps(j)
    with open('/root/HNASAPI/Billing/billing_' + sigla + '.csv', 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['filesystem', 'diskUsage', 'limit'])
        writer.writeheader()

        if sigla in data:
            for fs in fslist['filesystems']:
                fsname = fs['label']
                fsid = []
                fsid.append([fs['virtualServerId'], fs['filesystemId']])
                if sigla in str(fsname):
                    for i in range(len(fsid)):
                        urlgetqta = BASE_URL.format(urllib.parse.quote(storage))
                        urlgetqta += 'quotas/' + str(fsid[i][0]) + '/filesystem/' + str(fsid[i][1])
                        reply = requests.request("GET", urlgetqta, headers=headers, data=payload, verify=False)
                        qtajson = reply.json()
                        if len(qtajson) == 1 and qtajson['virtualVolumeQuotas']:
                            for volum in qtajson['virtualVolumeQuotas']:
                                size_type = SIZE_UNIT.GB
                                diskUsage = convert_unit(volum['quota']['diskUsage'], size_type)
                                limit = convert_unit(volum['quota']['diskUsageThreshold']['limit'], size_type)
                                writer.writerow({'filesystem': fsname, 'diskUsage': diskUsage, 'limit': limit})
                        else:
                            print("There is no quota for volume " + fsname)
                else:
                    continue
        else:
            imprimeErro(storage, sigla)
            return exit(1)

    print('Relatorio de billing do Storage ' + sigla + ' gerado!'
'Billing enviado por E-mail')
    subprocess.call('mail -s "HNAS Billing" -a ""/root/HNASAPI/Billing/billing_' + sigla + '.csv"" '
                    '-r "root@stsprobe01" < "/root/HNASAPI/tmp/message" '
                    "TS_BRA_STO_SUPPORT@t-systems.com", shell=True)

def getBilling(storage, apikey, sigla):


    def imprimeErro(storage, sigla):
        mensagem = print('Não existem filesystems com a sigla ' + sigla + ' no Storage ' + storage)
        return mensagem

    class SIZE_UNIT(enum.Enum):
        BYTES = 1
        KB = 2
        MB = 3
        GB = 4

    def convert_unit(size_in_bytes, unit):
        """ Convert the size from bytes to other units like KB, MB or GB"""
        if unit == SIZE_UNIT.KB:
            return size_in_bytes//1024
        elif unit == SIZE_UNIT.MB:
            return size_in_bytes//(1024*1024)
        elif unit == SIZE_UNIT.GB:
            return size_in_bytes//(1024*1024*1024)
        else:
            return size_in_bytes

    payload = {}
    headers = {
        'X-Api-Key': apikey
    }
    urlgetfs = BASE_URL.format(urllib.parse.quote(storage))
    urlgetfs += 'filesystems'
    response = requests.request("GET", urlgetfs, headers=headers, data=payload, verify=False)
    fslist = response.json()
    j = json.loads(response.text)
    data = json.dumps(j)
    with open('/root/HNASAPI/Billing/billing_' + sigla + '.csv', 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['filesystem', 'Vivol', 'diskUsage(GB)', 'limit(GB)'])
        writer.writeheader()

        if sigla in data:
            for fs in fslist['filesystems']:
                fsname = fs['label']
                if sigla in str(fsname):
                    fsid = []
                    fsid.append([fs['virtualServerId'], fs['filesystemId']])
                    for i in range(len(fsid)):
                        urlgetoid = BASE_URL.format(urllib.parse.quote(storage))
                        urlgetoid += 'virtual-volumes/' + str(fsid[i][0]) + '/' + str(fsid[i][1])
                        reply = requests.request("GET", urlgetoid, headers=headers, data=payload, verify=False)
                        oidjsn = reply.json()
                        if len(oidjsn) == 1 and oidjsn['virtualVolumes']:
                            for vivol in oidjsn['virtualVolumes']:
                                size_type = SIZE_UNIT.GB
                                vvname = vivol['name']
                                uvc = convert_unit(vivol['usageVolumeCapacity'], size_type)
                                tvc = convert_unit(vivol['totalVolumeCapacity'], size_type)
                                writer.writerow({'filesystem': fsname, 'Vivol': vvname,
                                                 'diskUsage(GB)': uvc, 'limit(GB)': tvc})
                        else:
                            print("No vivol for volume: " + fsname)
                            continue
                else:
                    continue
        else:
            imprimeErro(storage, sigla)
            return exit(1)
    print('Relatorio de billing do cliente ' + sigla + ' gerado!\n\
        Path: /root/HNASAPI/Billing/billing_' + sigla + '.csv')
    file = '/root/HNASAPI/Billing/billing_' + sigla + '.csv'
    subprocess.call('mail -s "HNAS Billing" -a ""/root/HNASAPI/Billing/billing_' + sigla + '.csv"" '
                    '-r "root@stsprobe01" < "/root/HNASAPI/tmp/message" ' 
                    "TS_BRA_STO_SUPPORT@t-systems.com", shell=True)

def getbillingbkp(storage, apikey):

    class SIZE_UNIT(enum.Enum):
        BYTES = 1
        KB = 2
        MB = 3
        GB = 4

    def convert_unit(size_in_bytes, unit):
        """ Convert the size from bytes to other units like KB, MB or GB"""
        if unit == SIZE_UNIT.KB:
            return size_in_bytes//1024
        elif unit == SIZE_UNIT.MB:
            return size_in_bytes//(1024*1024)
        elif unit == SIZE_UNIT.GB:
            return size_in_bytes//(1024*1024*1024)
        else:
            return size_in_bytes

    payload = {}
    headers = {
        'X-Api-Key': apikey
    }
    urlgetfs = BASE_URL.format(urllib.parse.quote(storage))
    urlgetfs += "filesystems"
    response = requests.request("GET", urlgetfs, headers=headers, data=payload, verify=False)
    fslist = response.json()
    with open('/root/HNASAPI/Billing/billing_' + storage + '.csv', 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['filesystem', 'diskUsage', 'limit'])
        writer.writeheader()

        for item in fslist['filesystems']:
            size_type = SIZE_UNIT.GB
            fsname = item['label']
            capacity = convert_unit(item['capacity'], size_type)
            usedCapacity = convert_unit(item['usedCapacity'], size_type)
            writer.writerow({'filesystem': fsname,'diskUsage': capacity, 'limit': usedCapacity})
    f.close()
    print('Relatorio de billing do Storage ' + storage + ' gerado!\n\
        Path: /root/HNASAPI/Billing/billing_' + storage + '.csv')


def main():

    # Menu para escolha do Storage

    while True:
        try:
            storage = storagetst = int(input('\n1 - HNCL01\n2 - HNCL02\n3 - HNCLBKP\nEscolha um Storage: '))
        except ValueError:
            print('"Entrada invalida"')
            continue
        else:
            if int(storage) == 1:
                storage = HNCL01
                apikey = APIKEY1
                break
            elif int(storage) == 2:
                storage = HNCL02
                apikey = APIKEY2
                break
            elif int(storage) == 3:
                storage = HNCLBKP
                apikey = APIKEY3
                break
            else:
                print('Escolha uma opcao entre 1 e 3')
                continue

        # Distribui chamada de funcao com base em op

    def case1():
        while True:
            try:
                sigla = str(input('SIGLAS:\nKRTN\nINTF\nATNT\nTSVM\nDigite o cliente desejado: '))
            except ValueError:
                print("Entrada invalida")
                continue
            else:
                return getfssnap(storage, apikey, sigla)

    def case2():
        if int(storagetst) == 3:
            return getbillingbkp(storage, apikey)
        else:
            while True:
                try:
                    sigla = str(input('SIGLAS:\nKRTN\nINTF\nATNT\nTSVM\nDigite o cliente desejado: '))
                except ValueError:
                    print('Entrada invalida!')
                    continue
                else:
                    if sigla.upper() == 'TSVM' or sigla.upper() == 'INTF':
                        return getBillingQuota(storage, apikey, sigla)
                    elif sigla.upper() == 'KRTN' or sigla.upper() == 'ATNT':
                        return getBilling(storage, apikey, sigla)

    def case3():
        print(op)

    def case4():
        print(op)

    def defineOption(op):
        options = {
            1: case1,
            2: case2,
            3: case3,
            4: case4
        }
        func = options.get(op, lambda: "Invalid option")
        return func()

    # Exibe segundo menu de opcoes
    # Armazena opcao em op
    while True:
        try:
            op = int(input('1 - GET Customer Snapshot Report\n\
2 - GET Billing\n\
3 - GET \n\
4 - GET \n\
Escolha uma opcao: '))
        except ValueError:
            print('Entrada invalida!')
            continue
        else:
            if 1 <= op < 5:
                return defineOption(op)
            else:
                print('Digite um valor entre 1 e 4')
                continue






if __name__ == "__main__":
    main()
