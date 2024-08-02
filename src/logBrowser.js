import React from 'react';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';

import basePage from './basePage.js';

import './css/styles.css';

class LoggerPage extends basePage {
  constructor(props, useSocketIO = true) {
    super(props, useSocketIO)
    this.state = {
      loading: false,
      waiting: false,
      TlogFiles: [],
      BinlogFiles: [],
      KMZlogFiles: [],
      error: null,
      infoMessage: null,
      diskSpaceStatus: "",
      conversionLogStatus: 'N/A',
      doLogConversion: true
    }

    // Socket.io client for reading update values
    this.socket.on('LogConversionStatus', function (msg) {
      this.setState({ conversionLogStatus: msg })
    }.bind(this))
    this.socket.on('reconnect', function () {
      // refresh state
      this.componentDidMount()
    }.bind(this))
  }

  handleDoLogConversion = event => {
    // user clicked enable/disable log conversion
    fetch('/api/logconversion', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        doLogConversion: !this.state.doLogConversion,
      })
    }).then(response => response.json()).then(state => { this.setState(state) });
  }

  componentDidMount() {
    fetch(`/api/logfiles`).then(response => response.json()).then(state => { this.setState(state); this.loadDone() });
    fetch(`/api/diskinfo`).then(response => response.json()).then(state => { this.setState(state) });
    fetch(`/api/logconversioninfo`).then(response => response.json()).then(state => { this.setState(state); this.loadDone() })
  }

  renderTitle() {
    return "Flight Log Browser";
  }

  // create a function to send logs to the API endpoint
  sendLog = (log) => {
    const formattedTime = new Date(log.modified).toISOString();
    // Step 1: Download the log file
    fetch(this.state.url + "/logdownload/" + log.key)


      
      .then(response => response.blob())  // Convert response to blob
      .then(blob => {
        // Create a FormData object and append the downloaded file
        const formData = new FormData();
        formData.append('droneid', 'ddh123jk');
        formData.append('FileField', blob, log.name); // Append blob as file with its name
        formData.append('time', formattedTime);
  
        // Step 2: Send the downloaded file
        return fetch('https://cbweb.onrender.com/api/dronedata/', {
          method: 'POST',
          body: formData,
        });
      })
      .then(response => response.json())
      .then(result => {
        console.log('Success:', result);
      })
      .catch(error => {
        console.error('Error:', error);
      });
  }
  

  // create an HTML table from a list of logfiles
  renderLogTableData(logfilelist, isBinLog = false) {
    return logfilelist.map((log, index) => {
      return (
        <tr key={log.key}>
          <td><a href={this.state.url + "/logdownload/" + log.key} download>{log.name}</a></td>
          <td>{log.size} KB</td>
          <td>{log.modified}</td>
          {isBinLog && (
            <td>
              <Button onClick={() => this.sendLog(log)}>Send</Button>
            </td>
          )}
        </tr>
      )
    });
  }

  clearLogs = (event) => {
    const id = event.target.id;
    this.setState({ waiting: true }, () => {
      fetch('/api/deletelogfiles', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logtype: id,
        })
      }).then(response => response.json())
        .then(result => {
          this.componentDidMount();
          this.setState({ waiting: false });
        })
        .catch(error => {
          this.setState({ waiting: false, error: "Error deleting logfiles: " + error });
        });
    });
    event.preventDefault();
  }

  renderContent() {
    return (
      <div style={{ width: 600 }}>
        <p><i>Save and download flight logs</i></p>
        <p>Disk Space: {this.state.diskSpaceStatus}</p>
        <h3>Telemetry Logs</h3>
        <p>Telemetry Logging can be enabled or disabled in the "Flight Controller" page.</p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button id='tlog' onClick={this.clearLogs}>Clear inactive logs</Button>
          </div>
        </div>
        <Table id='Tlogfile' striped bordered hover size="sm">
          <thead>
            <tr><th>File Name</th><th>Size</th><th>Modified</th></tr>
          </thead>
          <tbody>
            {this.renderLogTableData(this.state.TlogFiles)}
          </tbody>
        </Table>
        <br />
        <h3>Bin Logs</h3>
        <p>This requires the <code>LOG_BACKEND_TYPE</code> parameter in ArduPilot set to <code>Mavlink</code>. A high baudrate to the flight controller (921500 or greater) is required.</p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button id='binlog' onClick={this.clearLogs}>Clear inactive logs</Button>
          </div>
        </div>
        <Table id='Binlogfile' striped bordered hover size="sm">
          <thead>
            <tr><th>File Name</th><th>Size</th><th>Modified</th><th>Action</th></tr>
          </thead>
          <tbody>
            {this.renderLogTableData(this.state.BinlogFiles, true)}
          </tbody>
        </Table>
        <br />
        <h3>KMZ Files</h3>
        <p>KMZ files created from the Telemetry Logs every 20 seconds.</p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button onClick={this.handleDoLogConversion} className="btn btn-primary">{this.state.doLogConversion === true ? 'Disable' : 'Enable'}</Button>
          </div>
        </div>
        <p>Status: {this.state.conversionLogStatus}</p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button id='kmzlog' onClick={this.clearLogs}>Clear KMZ files</Button>
          </div>
        </div>
        <Table id='KMZlogfile' striped bordered hover size="sm">
          <thead>
            <tr><th>File Name</th><th>Size</th><th>Modified</th></tr>
          </thead>
          <tbody>
            {this.renderLogTableData(this.state.KMZlogFiles)}
          </tbody>
        </Table>
        <br />
      </div>
    );
  }
}

export default LoggerPage;

