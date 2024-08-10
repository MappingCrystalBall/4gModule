// import React from 'react';
// import Select from 'react-select';
// import Button from 'react-bootstrap/Button';
// import Table from 'react-bootstrap/Table';
// import io from 'socket.io-client';

// import basePage from './basePage.js';

// import './css/styles.css';

// class FCPage extends basePage {
//   constructor(props, useSocketIO = true) {
//     super(props, useSocketIO);
//     this.state = {
//       telemetryStatus: this.props.telemetryStatus,
//       serialPorts: [],
//       baudRates: [],
//       mavVersions: [],
//       serialPortSelected: null,
//       baudRateSelected: null,
//       mavVersionSelected: null,
//       enableHeartbeat: null,
//       enableTCP: null,
//       FCStatus: {},
//       UDPoutputs: [],
//       addrow: "",
//       loading: true,
//       error: null,
//       infoMessage: null,
//       socketioStatus: false,
//       usedSocketIO: true,
//       enableUDPB: false,
//       UDPBPort: 14550,
//       enableDSRequest: false,
//       tlogging: false,
//       rollValues: [], // State to store roll values
//     }

//     // Initialize socket connection
//     this.socket = io('http://localhost:3000'); // Replace with your server URL

//     this.socket.on('connect', () => {
//       console.log('Socket connected');
//       this.setState({ loading: false });
//     });

//     this.socket.on('rollData', (data) => {
//       console.log(`Received roll data: ${data.roll}`);
//       if (data && data.roll !== undefined) {
//         this.setState(prevState => ({
//           rollValues: [...prevState.rollValues, data.roll]
//         }));
//       }
//     });

//     this.socket.on('disconnect', () => {
//       console.log('Socket disconnected');
//     });

//     this.socket.on('reconnect', () => {
//       console.log('Socket reconnected');
//       this.setState({ loading: false });
//     });
//   }

//   componentDidMount() {
//     fetch(`/api/FCDetails`)
//       .then(response => response.json())
//       .then(state => this.setState(state))
//       .catch(error => this.setState({ error }));

//     fetch(`/api/FCOutputs`)
//       .then(response => response.json())
//       .then(state => {
//         this.setState(state);
//         this.loadDone();
//       })
//       .catch(error => this.setState({ error }));
//   }

//   handleSerialPortChange = (value, action) => {
//     this.setState({ serialPortSelected: value });
//   }

//   handleBaudRateChange = (value, action) => {
//     this.setState({ baudRateSelected: value });
//   }

//   handleMavVersionChange = (value, action) => {
//     this.setState({ mavVersionSelected: value });
//   }

//   handleUseHeartbeatChange = (event) => {
//     this.setState({ enableHeartbeat: event.target.checked });
//   }

//   handleUseTCPChange = (event) => {
//     this.setState({ enableTCP: event.target.checked });
//   }

//   handleTloggingChange = (event) => {
//     this.setState({ tlogging: event.target.checked });
//   }

//   handleDSRequest = (event) => {
//     this.setState({ enableDSRequest: event.target.checked });
//   }

//   handleUseUDPBChange = (event) => {
//     this.setState({ enableUDPB: event.target.checked });
//   }

//   changeUDPBPort = (event) => {
//     this.setState({ UDPBPort: event.target.value });
//   }

//   handleSubmit = (event) => {
//     fetch('/api/FCModify', {
//       method: 'POST',
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         device: JSON.stringify(this.state.serialPortSelected),
//         baud: JSON.stringify(this.state.baudRateSelected),
//         mavversion: JSON.stringify(this.state.mavVersionSelected),
//         enableHeartbeat: this.state.enableHeartbeat,
//         enableTCP: this.state.enableTCP,
//         enableUDPB: this.state.enableUDPB,
//         UDPBPort: this.state.UDPBPort,
//         enableDSRequest: this.state.enableDSRequest,
//         tlogging: this.state.tlogging
//       })
//     })
//     .then(response => response.json())
//     .then(state => this.setState(state))
//     .catch(error => this.setState({ error }));
//   }

//   handleFCReboot = (event) => {
//     fetch('/api/FCReboot', {
//       method: 'POST',
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       }
//     }).catch(error => this.setState({ error }));
//   }

//   addUdpOutput = (event) => {
//     fetch('/api/addudpoutput', {
//       method: 'POST',
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         newoutputIP: this.state.addrow.split(":")[0],
//         newoutputPort: this.state.addrow.split(":")[1]
//       })
//     })
//     .then(response => response.json())
//     .then(state => this.setState(state))
//     .catch(error => this.setState({ error }));
//   }

//   removeUdpOutput = (val) => {
//     fetch('/api/removeudpoutput', {
//       method: 'POST',
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         removeoutputIP: val.IPPort.split(":")[0],
//         removeoutputPort: val.IPPort.split(":")[1]
//       })
//     })
//     .then(response => response.json())
//     .then(state => this.setState(state))
//     .catch(error => this.setState({ error }));
//   }

//   changeaddrow = event => {
//     const value = event.target.value;
//     this.setState({ addrow: value });
//   }

//   renderTitle() {
//     return "Flight Controller";
//   }

//   renderUDPTableData(udplist) {
//     return udplist.map((output, index) => (
//       <tr key={index}>
//         <td>{output.IPPort}</td>
//         <td><Button size="sm" id={index} onClick={() => this.removeUdpOutput(output)}>Delete</Button></td>
//       </tr>
//     ));
//   }

//   renderContent() {
//     return (
//       <div>
//         <h2>Serial Input</h2>
//         <p><i>Flight Controller connection to this device</i></p>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">Serial Device</label>
//           <div className="col-sm-8">
//             <Select
//               isDisabled={this.state.telemetryStatus}
//               onChange={this.handleSerialPortChange}
//               options={this.state.serialPorts}
//               value={this.state.serialPortSelected}
//             />
//           </div>
//         </div>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">Baud Rate</label>
//           <div className="col-sm-8">
//             <Select
//               isDisabled={this.state.telemetryStatus}
//               onChange={this.handleBaudRateChange}
//               options={this.state.baudRates}
//               value={this.state.baudRateSelected}
//             />
//           </div>
//         </div>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">MAVLink Version</label>
//           <div className="col-sm-8">
//             <Select
//               isDisabled={this.state.telemetryStatus}
//               onChange={this.handleMavVersionChange}
//               options={this.state.mavVersions}
//               value={this.state.mavVersionSelected}
//             />
//           </div>
//         </div>

//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <div className="col-sm-8">
//             <Button
//               disabled={this.state.serialPorts.length === 0}
//               onClick={this.handleSubmit}
//             >
//               {this.state.telemetryStatus ? "Stop Telemetry" : "Start Telemetry"}
//             </Button>
//           </div>
//         </div>

//         <br />
//         <h2>Telemetry Destinations</h2>
//         <p><i>Telemetry must be stopped before the below options can be edited.</i></p>
//         <h3>UDP Client</h3>
//         <p><i>Send telemetry to a specific IP:port. Use "UDP" option in Mission Planner.</i></p>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">Destination IP:Port</label>
//           <div className="col-sm-8">
//             <input
//               type="text"
//               value={this.state.addrow}
//               onChange={this.changeaddrow}
//             />
//             <Button
//               onClick={this.addUdpOutput}
//               disabled={this.state.addrow.length === 0}
//             >
//               Add
//             </Button>
//           </div>
//         </div>
//         <Table striped bordered hover>
//           <thead>
//             <tr>
//               <th>Destination IP:Port</th>
//               <th>Action</th>
//             </tr>
//           </thead>
//           <tbody>
//             {this.renderUDPTableData(this.state.UDPoutputs)}
//           </tbody>
//         </Table>

//         <h2>Settings</h2>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <div className="col-sm-4">
//             <label className="col-form-label">Use Heartbeat</label>
//             <input
//               type="checkbox"
//               onChange={this.handleUseHeartbeatChange}
//               checked={this.state.enableHeartbeat}
//             />
//           </div>
//           <div className="col-sm-4">
//             <label className="col-form-label">Use TCP</label>
//             <input
//               type="checkbox"
//               onChange={this.handleUseTCPChange}
//               checked={this.state.enableTCP}
//             />
//           </div>
//           <div className="col-sm-4">
//             <label className="col-form-label">Enable UDP Broadcast</label>
//             <input
//               type="checkbox"
//               onChange={this.handleUseUDPBChange}
//               checked={this.state.enableUDPB}
//             />
//           </div>
//         </div>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">UDP Broadcast Port</label>
//           <div className="col-sm-8">
//             <input
//               type="number"
//               value={this.state.UDPBPort}
//               onChange={this.changeUDPBPort}
//             />
//           </div>
//         </div>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">Enable Data Stream Requests</label>
//           <div className="col-sm-8">
//             <input
//               type="checkbox"
//               onChange={this.handleDSRequest}
//               checked={this.state.enableDSRequest}
//             />
//           </div>
//         </div>
//         <div className="form-group row" style={{ marginBottom: '5px' }}>
//           <label className="col-sm-4 col-form-label">Telemetry Logging</label>
//           <div className="col-sm-8">
//             <input
//               type="checkbox"
//               onChange={this.handleTloggingChange}
//               checked={this.state.tlogging}
//             />
//           </div>
//         </div>
//         <div className="form-group row">
//           <div className="col-sm-4">
//             <Button
//               onClick={this.handleFCReboot}
//             >
//               Reboot Flight Controller
//             </Button>
//           </div>
//         </div>

//         <h2>Roll Values</h2>
//         <div>
//           {this.state.rollValues.length === 0 ? (
//             <p>No roll values received yet.</p>
//           ) : (
//             <ul>
//               {this.state.rollValues.map((value, index) => (
//                 <li key={index}>sekhar: {value.toFixed(18)}</li>
//               ))}
//             </ul>
//           )}
//         </div>
//       </div>
//     );
//   }
// }

// export default FCPage;



import React from 'react';
import Select from 'react-select';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';
import io from 'socket.io-client';
import basePage from './basePage.js';
import './css/styles.css';
import GoogleMapComponent from './components/GoogleMapComponent';


class FCPage extends basePage {
  constructor(props, useSocketIO = true) {
    super(props, useSocketIO);
    this.state = {
      telemetryStatus: this.props.telemetryStatus,
      serialPorts: [],
      baudRates: [],
      mavVersions: [],
      serialPortSelected: null,
      baudRateSelected: null,
      mavVersionSelected: null,
      enableHeartbeat: null,
      enableTCP: null,
      FCStatus: {},
      UDPoutputs: [],
      addrow: "",
      loading: true,
      error: null,
      infoMessage: null,
      socketioStatus: false,
      usedSocketIO: true,
      enableUDPB: false,
      UDPBPort: 14550,
      enableDSRequest: false,
      tlogging: false,
      rollValue: null,
      lat: 17.494389,  // Store converted latitude
      lng: 78.142,     // Store converted longitude
    };

    this.socket = io('http://localhost:3000'); // Replace with your server URL

    this.socket.on('connect', () => {
      console.log('Socket connected');
      this.setState({ loading: false });
    });

    this.socket.on('rollData', (data) => {
      console.log(`Received roll data: ${data.roll}`);
      if (data && data.roll !== undefined) {
        this.setState({ rollValue: data.roll });
      }
    });
    this.socket.on('locationData', (data) => {
      console.log('Received location data:', data.lat, data.lng);
      if (data && data.lat !== undefined && data.lng !== undefined) {
        this.setState({
          lat: data.lat,
          lng: data.lng
        });
      }
    });
    
    

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    this.socket.on('reconnect', () => {
      console.log('Socket reconnected');
      this.setState({ loading: false });
    });
  }

  componentDidMount() {
    fetch(`/api/FCDetails`)
      .then(response => response.json())
      .then(state => this.setState(state))
      .catch(error => this.setState({ error }));

    fetch(`/api/FCOutputs`)
      .then(response => response.json())
      .then(state => {
        this.setState(state);
        this.loadDone();
      })
      .catch(error => this.setState({ error }));
  }

  handleSerialPortChange = (value, action) => {
    this.setState({ serialPortSelected: value });
  }

  handleBaudRateChange = (value, action) => {
    this.setState({ baudRateSelected: value });
  }

  handleMavVersionChange = (value, action) => {
    this.setState({ mavVersionSelected: value });
  }

  handleUseHeartbeatChange = (event) => {
    this.setState({ enableHeartbeat: event.target.checked });
  }

  handleUseTCPChange = (event) => {
    this.setState({ enableTCP: event.target.checked });
  }

  handleTloggingChange = (event) => {
    this.setState({ tlogging: event.target.checked });
  }

  handleDSRequest = (event) => {
    this.setState({ enableDSRequest: event.target.checked });
  }

  handleUseUDPBChange = (event) => {
    this.setState({ enableUDPB: event.target.checked });
  }

  changeUDPBPort = (event) => {
    this.setState({ UDPBPort: event.target.value });
  }

  handleSubmit = (event) => {
    fetch('/api/FCModify', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device: JSON.stringify(this.state.serialPortSelected),
        baud: JSON.stringify(this.state.baudRateSelected),
        mavversion: JSON.stringify(this.state.mavVersionSelected),
        enableHeartbeat: this.state.enableHeartbeat,
        enableTCP: this.state.enableTCP,
        enableUDPB: this.state.enableUDPB,
        UDPBPort: this.state.UDPBPort,
        enableDSRequest: this.state.enableDSRequest,
        tlogging: this.state.tlogging
      })
    })
    .then(response => response.json())
    .then(state => this.setState(state))
    .catch(error => this.setState({ error }));
  }

  handleFCReboot = (event) => {
    fetch('/api/FCReboot', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      }
    }).catch(error => this.setState({ error }));
  }

  addUdpOutput = (event) => {
    fetch('/api/addudpoutput', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        newoutputIP: this.state.addrow.split(":")[0],
        newoutputPort: this.state.addrow.split(":")[1]
      })
    })
    .then(response => response.json())
    .then(state => this.setState(state))
    .catch(error => this.setState({ error }));
  }

  removeUdpOutput = (val) => {
    fetch('/api/removeudpoutput', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        removeoutputIP: val.IPPort.split(":")[0],
        removeoutputPort: val.IPPort.split(":")[1]
      })
    })
    .then(response => response.json())
    .then(state => this.setState(state))
    .catch(error => this.setState({ error }));
  }

  changeaddrow = event => {
    const value = event.target.value;
    this.setState({ addrow: value });
  }
  // getMapUrl() {
  //   const { lat, lng } = this.state;
  //   const formattedLat = lat.toFixed(6);
  //   const formattedLng = lng.toFixed(6);
  
  //   return `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3806.3261743167027!2d${formattedLng}!3d${formattedLat}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bcc56c394395715%3A0xa2e2d56e30d4e0cc!2sF4VR%2BMQG%2C%20Sr.%20Club%20Rd%2C%20Yeddumailaram%2C%20Telangana%20502205%2C%20India!5e0!3m2!1sen!2sus!4v1691851802333!5m2!1sen!2sus&center=${formattedLat},${formattedLng}&zoom=17`;
  // }
  

  renderTitle() {
    return "Flight Controller";
  }

  renderUDPTableData(udplist) {
    return udplist.map((output, index) => (
      <tr key={index}>
        <td>{output.IPPort}</td>
        <td><Button size="sm" id={index} onClick={() => this.removeUdpOutput(output)}>Delete</Button></td>
      </tr>
    ));
  }
 

  renderContent() {
    return (
      <div>
        <h2>Serial Input</h2>
        <p><i>Flight Controller connection to this device</i></p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <label className="col-sm-4 col-form-label">Serial Device</label>
          <div className="col-sm-8">
            <Select
              isDisabled={this.state.telemetryStatus}
              onChange={this.handleSerialPortChange}
              options={this.state.serialPorts}
              value={this.state.serialPortSelected}
            />
          </div>
        </div>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <label className="col-sm-4 col-form-label">Baud Rate</label>
          <div className="col-sm-8">
            <Select
              isDisabled={this.state.telemetryStatus}
              onChange={this.handleBaudRateChange}
              options={this.state.baudRates}
              value={this.state.baudRateSelected}
            />
          </div>
        </div>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <label className="col-sm-4 col-form-label">MAVLink Version</label>
          <div className="col-sm-8">
            <Select
              isDisabled={this.state.telemetryStatus}
              onChange={this.handleMavVersionChange}
              options={this.state.mavVersions}
              value={this.state.mavVersionSelected}
            />
          </div>
        </div>

        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button
              disabled={this.state.serialPorts.length === 0}
              onClick={this.handleSubmit}
            >
              {this.state.telemetryStatus ? "Stop Telemetry" : "Start Telemetry"}
            </Button>
          </div>
        </div>

        <br />
        <h2>Telemetry Destinations</h2>
        <p><i>Telemetry must be stopped before the below options can be edited.</i></p>
        <h3>UDP Client</h3>
        <p><i>Send telemetry to a specific IP:port. Use "UDP" option in Mission Planner.</i></p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <label className="col-sm-4 col-form-label">Destination IP:Port</label>
          <div className="col-sm-8">
            <input
              type="text"
              className="form-control"
              disabled={this.state.telemetryStatus}
              value={this.state.addrow}
              onChange={this.changeaddrow}
            />
          </div>
        </div>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button
              size="sm"
              disabled={this.state.telemetryStatus}
              onClick={this.addUdpOutput}
            >
              Add
            </Button>
          </div>
        </div>
        <div className="row">
          <div className="col-md-12">
            <Table striped bordered hover>
              <thead>
                <tr>
                  <th>IP:Port</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {this.renderUDPTableData(this.state.UDPoutputs)}
              </tbody>
            </Table>
          </div>
        </div>

        <br />
        <h3>UDP Broadcast</h3>
        <p><i>Send telemetry to all devices on this subnet.</i></p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <label className="col-sm-4 col-form-label">Broadcast Port</label>
          <div className="col-sm-8">
            <input
              type="text"
              className="form-control"
              disabled={this.state.telemetryStatus}
              value={this.state.UDPBPort}
              onChange={this.changeUDPBPort}
            />
          </div>
        </div>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <input
              type="checkbox"
              disabled={this.state.telemetryStatus}
              checked={this.state.enableUDPB}
              onChange={this.handleUseUDPBChange}
            />
            <label className="form-check-label" style={{ marginLeft: '10px' }}>Enable UDP Broadcast</label>
          </div>
        </div>

        <br />
        <h3>Debug</h3>
        <p><i>Reboot the flight controller.</i></p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <Button
              size="sm"
              disabled={this.state.telemetryStatus}
              onClick={this.handleFCReboot}
            >
              Reboot Flight Controller
            </Button>
          </div>
        </div>

        <br />
        <h2>Roll value</h2>
        <p><i>Latest roll value received from MAVLink:</i></p>
        <div className="form-group row" style={{ marginBottom: '5px' }}>
          <div className="col-sm-8">
            <p>Roll: {this.state.rollValue !== null ? this.state.rollValue : 'No data'}</p>
          </div>
        </div>

        <br />
        <br />
        <h2>Coordinates</h2>
        <p>Latitude: {this.state.lat}</p>
        <p>Longitude: {this.state.lng}</p>

        <br />
        <h2>Google Map</h2>
        <script async
    src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places">
  </script>
        <GoogleMapComponent lat={this.state.lat} lng={this.state.lng} />
        {/* <div style={{ width: '100%', height: '400px' }}>
          <iframe
           src={this.getMapUrl()}
            width="100%"
            height="100%"
            style={{ border: 0 }}
            allowFullScreen=""
            loading="lazy"
          ></iframe>
        </div> */}
      </div>
    );
  }
}

export default FCPage;

