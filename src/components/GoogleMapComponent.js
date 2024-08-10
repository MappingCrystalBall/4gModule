import React from 'react';
import { GoogleMap, Marker, useLoadScript } from '@react-google-maps/api';

const GoogleMapComponent = ({ lat, lng }) => {
  const { isLoaded } = useLoadScript({
    googleMapsApiKey: "YOUR_API_KEY", // Replace with your Google Maps API key
  });

  if (!isLoaded) return <div>Loading...</div>;

  return (
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '400px' }}
      zoom={15}
      center={{ lat, lng }}
    >
      <Marker position={{ lat, lng }} label={`Lat: ${lat}, Lng: ${lng}`} />
    </GoogleMap>
  );
};

export default GoogleMapComponent;
