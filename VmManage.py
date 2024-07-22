# -*- coding: utf-8 -*-
from pyVim.connect import SmartConnectNoSSL
from pyVmomi import vim
from tools_for_import_ova import get_resource_pool, get_datastore, OvfHandler
import time, tasks, pchelper

class VmManage(object):

    def __init__(self, host, user, password, port):
        self.host = host
        self.user = user
        self.pwd = password
        self.port = port
        try:
            self.client = SmartConnectNoSSL(host=host,
                                            user=user,
                                            pwd=password,
                                            port=443
                                            )
        except:
            raise Exception ("ESXi connection failed")
    def vm_power_on(self, vm_name):
        VM = pchelper.get_obj(self.client.content, [vim.VirtualMachine], vm_name)
        if VM is None:
            raise SystemExit("Unable to locate VirtualMachine. :" + vm_name)
        if format(VM.runtime.powerState) == "poweredOff":
            print("Attempting to power on {0}".format(VM.name))
            TASK = VM.PowerOnVM_Task()
            tasks.wait_for_tasks(self.client, [TASK])
            print("{0}".format(TASK.info.state))
        else :
            print("{0} Already Powered On".format(vm_name))
    
    def vm_power_off(self, vm_name):
        VM = pchelper.get_obj(self.client.content, [vim.VirtualMachine], vm_name)
        if VM is None:
            raise SystemExit("Unable to locate VirtualMachine. :" + vm_name)
        if format(VM.runtime.powerState) == "poweredOn":
            print("Attempting to power off {0}".format(VM.name))
            TASK = VM.PowerOffVM_Task()
            tasks.wait_for_tasks(self.client, [TASK])
            print("{0}".format(TASK.info.state))
        else :
            print("{0} Already Powered Off".format(vm_name))

    def destroy_vm(self, vm_name):
        VM = pchelper.get_obj(self.client.content, [vim.VirtualMachine], vm_name)
        if VM is None:
            raise SystemExit("Unable to locate VirtualMachine. :" + vm_name)
        if format(VM.runtime.powerState) == "poweredOn":
            print("Attempting to power off {0}".format(VM.name))
            TASK = VM.PowerOffVM_Task()
            tasks.wait_for_tasks(self.client, [TASK])
            print("{0}".format(TASK.info.state))
        print("Destroying VM from vSphere.")
        TASK = VM.Destroy_Task()
        tasks.wait_for_tasks(self.client, [TASK])
        print("Done.")

    def create_vm_from_ova(self, ova_path):
        datacenter = self.client.content.rootFolder.childEntity[0]
        resourcePool = get_resource_pool(self.client, datacenter)
        datastore = get_datastore(datacenter)
        ovf_handle = OvfHandler(ova_path)
        ovf_manager = self.client.content.ovfManager
        cisp = vim.OvfManager.CreateImportSpecParams()
        cisr = ovf_manager.CreateImportSpec(
            ovf_handle.get_descriptor(), resourcePool, datastore, cisp)

        if cisr.error:
            print("The following errors will prevent import of this OVA:")
            for error in cisr.error:
                print("%s" % error)
            return 1

        ovf_handle.set_spec(cisr)

        lease = resourcePool.ImportVApp(cisr.importSpec, datacenter.vmFolder)
        while lease.state == vim.HttpNfcLease.State.initializing:
            print("Waiting for lease to be ready...")
            time.sleep(1)

        if lease.state == vim.HttpNfcLease.State.error:
            print("Lease error: %s" % lease.error)
            return 1
        if lease.state == vim.HttpNfcLease.State.done:
            return 0

        print("Starting deploy...")
        return ovf_handle.upload_disks(lease, self.host)

    def get_vm_ip(self, vm_name):
        VM = pchelper.get_obj(self.client.content, [vim.VirtualMachine], vm_name)
        while VM.summary.guest.ipAddress ==None:
            time.sleep(5)
        return VM.summary.guest.ipAddress


  