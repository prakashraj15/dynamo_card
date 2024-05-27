import React, {useState} from 'react';
import axios from 'axios';
import Flashcard from './Flashcard.jsx';


function App() {

  const [youtubeLink, setYoutubeLink] = useState("");
  const [KeyConcepts, setKeyConcepts] = useState([]);

  const handleLinkChange = (event) => {
    setYoutubeLink(event.target.value);
  };

  const sendLink = async () => {
    try{
      const response = await axios.post("http://localhost:8000/analyze_videos ", {youtube_link: youtubeLink});
      const data = response.data;
      if (data.key_concepts && Array.isArray(data.key_concepts)) {
        setKeyConcepts(data.key_concepts);
      }
      else {
        console.error("Data doews not contain key concepts: ", data);
        setKeyConcepts([]);
      }
    } catch (error) {
      console.log(error);
      setKeyConcepts([]);
    }

  };

  const discardFlashcards = (index) => {
    setKeyConcepts(currentKeyConcepts => currentKeyConcepts.filter((_, i) => i !== index));
  };
  
  return(
    <div className='App'>
      <h1> YouTube Link to Flashcards Generator</h1>
      <div className = "input-container">
        <input
          type="text"
          placeholder="Enter YouTube Link"
          value={youtubeLink}
          onChange={handleLinkChange}
          className='inputField'
        />
        <button onClick={sendLink} className='button'>Generate Flashcards</button>
      </div>
      <div className="flashcards-container">
        {KeyConcepts.map((concept, index) => {
          <Flashcard 
            key = {index}
            term = {concept.term}
            definition = {concept.definition}
            onDiscord = {() => discardFlashcards(index)}
          />
        })}
      </div>
    </div>
  );
}
  
export default App;