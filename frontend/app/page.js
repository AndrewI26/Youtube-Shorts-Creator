'use client'

import { useState } from 'react'
import "./styles.css"

export default function Home() {
  const [subreddit, setSubreddit] = useState('')
  const [postTitle, setPostTitle] = useState('')
  const [content, setContent] = useState('')
  const [videoChoice, setVideoChoice] = useState('subwaySurfers')

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState()
  const [videoURL, setVideoURL] = useState()

  const videoStyle = {
    width: '450px',
    height: '800px'
  }
  const containerStyle = {
    backgroundColor: "#FFFFFF",
    padding: '50px 100px',
    borderRadius: '25px'
  }
  const selectionStyle = {
    display: 'flex',
    flexDirection: 'column',
  }
  const optionStyle = {
    color: "#34a265",
  }
  const selectStyle = {
    appearance: 'none',
    padding: '10px',
    font: 'inter',
    weight: '700',
    color: "#34a265",
    border: "2px black solid",
    fontSize: '16px',
    borderRadius: "10px", 
    backgroundColor: "#FFFFFF",
  }
  const boxStyle = {
    fontSize: "19px"
  }
  const inputStyle = {
    borderRadius: '7px',
    borderColor: 'black',
    padding: '10px',
    fontSize: '16px',
    color: '#34a265',
    border: "2px black solid",
    marginBottom: '20px'
  }
  const buttonStyle = {
    backgroundColor: "#34a265",
    fontStyle: "inter",
    color: "#FFFFFF",
    padding: "15px",
    borderRadius: '20px',
    fontWeight: "600",
    fontSize: "30px",
    margin: "15px",
    border: "10px white solid"
  } 
  const buttonsStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  }
  const flexStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }

  const clear = (e) => {
    e.preventDefault()
    setSubreddit('')
    setPostTitle('')
    setContent('')
    setVideoChoice('subwaySurfers')
  }
  
  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    try {
      // Make API call
      const fileName = content.slice(0,8)
      const bodyObject = {
        file_name: fileName,
        content: content,
        post_title: postTitle,
        subreddit: subreddit,
        video_choice: videoChoice,
      }
      const res = await fetch('http://127.0.0.1:8000/shorts/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bodyObject),
      })
      
      if (!res.ok) {
        setError(res.error)
        throw new Error(`Response status: ${res.status}`)
      }
      setResponse(res)
      setLoading(false)
      const blob = await res.blob();
      const videoUrl = URL.createObjectURL(blob);
      setVideoURL(videoUrl)
      console.log("created url blob")
      console.log(videoURL)
    } catch(error) {
      console.log(videoURL)
    }
  }
      

  return (
    <main>
      <div style={containerStyle}>
        {error && <h1>{error}</h1>}
        {loading || videoURL? <h1>Please wait... loading.</h1> : 
        <div>
          <h1>Fill out the details below to generate a video:</h1>
          <form onSubmit={handleSubmit}>
            <div style={selectionStyle}>
              <label htmlFor="subreddit" style={boxStyle}>Subreddit:</label>
              <input
                type="text"
                id="subreddit"
                value={subreddit}
                style={inputStyle}
                onChange={e => setSubreddit(e.target.value)}
              />
            </div>
            <div style={selectionStyle}>
              <label htmlFor="postTitle" style={boxStyle}>Post title:</label>
              <input
                type="text"
                id="postTitle"
                value={postTitle}
                style={inputStyle}
                onChange={e => setPostTitle(e.target.value)}
              />
            </div>
            <div style={selectionStyle}>
              <label htmlFor="content" style={boxStyle}>Body:</label>
              <textarea
                type="text"
                id="content"
                value={content}
                style={inputStyle}
                onChange={e => setContent(e.target.value)}
              />
            </div>
            <div style={selectionStyle}>
              <label htmlFor="videoChoice" style={boxStyle}>Video Choice:</label>
              <select id="choices" style={selectStyle} value={videoChoice} onChange={e => setVideoChoice(e.target.value)}>
                <option value="subwaySurfers" style={optionStyle}>Subway Surfers</option>
                <option value="minecraftParkor" style={optionStyle}>Minecraft Parkor</option>
                <option value="mobileGame" style={optionStyle}>Satisfying Mobile Game</option>
              </select>
            </div>
            <div style={buttonsStyle}>
              <button type='submit' style={buttonStyle}>Submit</button>
              <button style={buttonStyle} onClick={clear}>Clear</button>
            </div>
          </form>
        </div>
        }
        {loading && <div style={flexStyle}><div class="loader"></div></div>}
        {videoURL &&
        <div>
          <video controls style={videoStyle}>
            <source src={videoURL} type="video/mp4" />
            Your browser does not support the video tag.
            <a href={videoURL} download="clip.mp4">
              <button>Download Video</button>
            </a>
          </video>
        </div>}
      </div>
    </main>
  );
}
