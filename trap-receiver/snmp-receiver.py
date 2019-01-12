from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from pysnmp.smi import builder, view, compiler, rfc1902
from pysmi import debug
import re
import pyodbc
import os 
from datetime import datetime
import logging
from os import getenv
import time


class TrapEvent(object):
    cnxn = None
    cursor = None

    """TrapEvent Class"""
    def __init__(self):
        self.event_date = time.strftime("%Y-%m-%d %H:%M:%S")
        self.sender = ""
        # self.createDBConnection()
    
    def createDBConnection(self):
        try:
            if not (self.cnxn and self.cursor): 
                self.cnxn = pyodbc.connect('DRIVER={FreeTDS};SERVER=SERVERDOMAINNAME;PORT=3180;DATABASE=DBNAME;UID=USERID;PWD=PWD;TDS_Version=7.0')
                self.cursor = self.cnxn.cursor()
        except:
            logging.error("Error on connection Creation")


    def persistToDB(self):
        try:
            event_date = self.mode_options[self.event_date]
            if (self.cLApRogueApMacAddress != None or self.cLApRogueApMacAddress != ""):
                self.cursor.execute("INSERT INTO [dbo].[TABLE] ([event_date], [sender]) VALUES('{}',{})".format(self.cLApName, self.sender))
                self.cnxn.commit()
            else:
                print("Not enough information to save")
        except Exception as ex:
            print("Error on INSERT TRAP")
            print(str(ex))

    def persistLogToDB(self,text):
        try:
            self.cursor.execute("INSERT INTO [dbo].[LOGTABLE]([log])VALUES('{}','{}')".format(text))
            self.cnxn.commit()
        except Exception as ex:
            logging.error(str(ex))
            print("Error on INSERT LOG")
            print(str(ex))
            

    def persistToLog(self):
        try:
            logging.info('cLApName --> {}'.format(self.cLApName))
            logging.info('cLApRogueApMacAddress --> {}'.format(self.cLApRogueApMacAddress))
            logging.info('date --> {}'.format(self.event_date))
        except:
            logging.error(':/')



def parseMAC(MacAddress):
    try:
        intMac = int(MacAddress,16)
        readableMACaddress = ':'.join('%02X' % ((intMac >> 8*i) & 0xff) for i in reversed(xrange(6)))
        return readableMACaddress
    except Exception as ex:
        print(str(ex))
        print("Error on MAC PARSE")
        return MacAddress




# noinspection PyUnusedLocal
def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    try:
        #Enables pysmi debugging
        #debug.setLogger(debug.Debug('reader'))

        # Assemble MIB viewer
        mibBuilder = builder.MibBuilder()
        mibViewController = view.MibViewController(mibBuilder)

        # Pre-load MIB modules we expect to work with 
        try:
            mibBuilder.loadModules('SNMPv2-MIB')
        except:
            logging.error("Fail loading mibs")

        
        # vars to store, match here the MIB field you need to save
        # cLApName = '1.3.6.1.4.1.9.9.513.1.1.1.1.5.0'
        # cLApRogueApMacAddress = '1.3.6.1.4.1.9.9.513.3.2.0'
        # cLApDot11IfType = '1.3.6.1.4.1.9.9.513.1.2.1.1.2.0'

        while wholeMsg:
            msgVer = int(api.decodeMessageVersion(wholeMsg))
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                print('Unsupported SNMP version %s' % msgVer)
                logging.error('Unsupported SNMP version %s' % msgVer)
                return
            reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(), )
            print('Notification message from %s:%s: ' % (transportDomain,transportAddress))
            logging.info('Notification message from %s:%s: ' % (transportDomain,
                                                            transportAddress))
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            if reqPDU.isSameTypeWith(pMod.TrapPDU()):
                if msgVer == api.protoVersion1:
                    varBinds = pMod.apiTrapPDU.getVarBinds(reqPDU)
                else:
                    varBinds = pMod.apiPDU.getVarBinds(reqPDU)
                    
                print('Var-binds:')
                logging.info('--------------------------------------------------------------------')
                logging.info('Var-binds:')

                trap = TrapEvent()
                for oid, val in varBinds:
                    print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
                trap.sender = str(transportAddress[0])
                # trap.persistToDB()
                    
                       
        return wholeMsg
    except Exception as e:
        trap = TrapEvent()
        logging.error(str(e))
        trap.persistLogToDB(str(e))

def main():

    logging.basicConfig(filename='traps.log',
                        filemode='w',
                        level=logging.ERROR,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    transportDispatcher = AsyncoreDispatcher()

    transportDispatcher.registerRecvCbFun(cbFun)

# UDP/IPv4
    transportDispatcher.registerTransport(udp.domainName, udp.UdpSocketTransport().openServerMode(('0.0.0.0', 162)))

# UDP/IPv6
    transportDispatcher.registerTransport(udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', 162)))

## Local domain socket
# transportDispatcher.registerTransport(
#    unix.domainName, unix.UnixSocketTransport().openServerMode('/tmp/snmp-manager')
# )

    transportDispatcher.jobStarted(1)

    try:
    # Dispatcher will never finish as job#1 never reaches zero
        transportDispatcher.runDispatcher()
    except:
        transportDispatcher.closeDispatcher()
        raise


if __name__ == "__main__":
    main()