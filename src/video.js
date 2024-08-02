import React, { Component } from 'react';

class VideoPage extends Component {
  render() {
    const videoFeedUrl = process.env.REACT_APP_VIDEO_FEED_URL || '/video_feed';
    return (
      <div>
        <h1>Live Video Feed</h1>
        <div>
          <img src='/api/video_feeed' alt="Live Video Feed" style={{ width: '100%' }} />
        </div>
      </div>
    );
  }
}

export default VideoPage;