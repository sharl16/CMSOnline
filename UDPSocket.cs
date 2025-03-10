/*
Created by Youssef Elashry to allow two-way communication between Python3 and Unity to send and receive strings

Feel free to use this in your individual or commercial projects BUT make sure to reference me as: Two-way communication between Python 3 and Unity (C#) - Y. T. Elashry
It would be appreciated if you send me how you have used this in your projects (e.g. Machine Learning) at youssef.elashry@gmail.com

Use at your own risk
Use under the Apache License 2.0

Modified by: 
Youssef Elashry 12/2020 (replaced obsolete functions and improved further - works with Python as well)
Based on older work by Sandra Fang 2016 - Unity3D to MATLAB UDP communication - [url]http://msdn.microsoft.com/de-de/library/bb979228.aspx#ID0E3BAC[/url]

Modified (3/2025) to work for a multiplayer implementation on Car Mechanic Simulator 2021.
*/

using UnityEngine;
using System.Collections;
using System;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using JetBrains.Annotations;

public class UDPSocket : MonoBehaviour
{
    public static UDPSocket Instance { get; private set; } // A signleton in order to get global access to UDPSocket class

    [HideInInspector] public bool isTxStarted = false;

    [SerializeField] string IP = "127.0.0.1"; // local host
    [SerializeField] int rxPort = 8000; // port to receive data from Python on
    [SerializeField] int txPort = 8001; // port to send data to Python on

    // Create necessary UdpClient objects
    UdpClient client;
    IPEndPoint remoteEndPoint;
    Thread receiveThread; // Receiving Thread

    public void SendData(string message) // Use to send data to Python
    {
        try
        {
            byte[] data = Encoding.UTF8.GetBytes(message);
            client.Send(data, data.Length, remoteEndPoint);
        }
        catch (Exception err)
        {
            print(err.ToString());
        }
    }

    void Awake()
    {
        // Create remote endpoint (to Matlab) 
        remoteEndPoint = new IPEndPoint(IPAddress.Parse(IP), txPort);

        // Create local client
        client = new UdpClient(rxPort);

        // local endpoint define (where messages are received)
        // Create a new thread for reception of incoming messages
        receiveThread = new Thread(new ThreadStart(ReceiveData));
        receiveThread.IsBackground = true;
        receiveThread.Start();

        // Initialize (seen in comments window)
        print("UDP Comms Initialised");
    }

    // Receive data, update packets received
    private void ReceiveData()
    {
        while (true)
        {
            try
            {
                IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
                byte[] data = client.Receive(ref anyIP);
                string text = Encoding.UTF8.GetString(data);
                print(text);
                ProcessInput(text);
            }
            catch (Exception err)
            {
                print(err.ToString());
            }
        }
    }

    private void ProcessInput(string input)
    {
        if (!isTxStarted) // First data arrived so tx started
        {
            isTxStarted = true;
        }

        // Input from ReceiveData() is processed here.

        // ==========================================

        // SessionType:

        if (input == "Set session as server.") // Server
        {
            if (sessionType != "Not Set")
            {
                Debug.Log($"sessionType is already set to {sessionType}. Cannot set Session to {input}.");
                return;
            }
            sessionType = "Server";
            Debug.Log($"Set sessionType to {sessionType}, session acting as Server");
            return;
        }

        if (input == "Set session as client.") // Client
        {
            if (sessionType != "Not Set")
            {
                Debug.Log($"sessionType is already set to {sessionType}. Cannot set Session to {input}.");
                return;
            }
            sessionType = "Client";
            Debug.Log($"Set sessionType to {sessionType}, session acting as Client");
            return;
        }

        if (input == "Set Player1 GameObject Position to: 100, 100, 100")
        {
            int index = input.IndexOf(':');
            if (index != -1) // Make sure ':' exists.
            {
                string result = input.Substring(index + 1).Trim();
                Debug.Log($"Set Player1 Gameobject position to: {result}");
            }
        }

        Debug.Log($"Data: '{input}' could not be processed: Unknown Input.");

        // ==========================================
    }

    //Prevent crashes - close clients and threads properly!
    void OnDisable()
    {
        if (receiveThread != null)
            receiveThread.Abort();

        client.Close();
    }

    // Additional Logic for CMS Online.
    public string sessionType = "Not Set";

    public void SendTestData()
    {
        Debug.Log("Sending Test Data");
        SendData("Test Data!");
        Debug.Log("Sent Test Data");
    }
}