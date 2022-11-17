import Head from 'next/head'
import styles from '../styles/Home.module.css'
import { useState } from 'react'

const REQUEST_CODE_URL = "https://noicemail.deepgram.com/codes"
const SIGNUP_URL = "https://noicemail.deepgram.com/users"
const TAGLINE = "It should've been a text anyways"
const options = [
  { display_name: "Summarize", slug: "summarize" },
  { display_name: "Detect topics", slug: "detect_topics" },
  { display_name: "Detect Language", slug: "detect_language" },
  { display_name: "Analyze Sentiment", slug: "analyze_sentiment" },
  { display_name: "Detect Entities", slug: "detect_entities" },
  { display_name: "Transcribe", slug: "transcribe" },
];

export default function Home() {
  const [code, setCode] = useState("")
  const [phoneNumber, setPhoneNumber] = useState("")
  const [showCodePrompt, setShowCodePrompt] = useState(false)
  const [noiceNumber, setNoiceNumber] = useState("")
  const [features, setFeatures] = useState({})

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (isPhoneNumberValid(phoneNumber)) {
      let data = { physical_phone_number: "+1" + phoneNumber }
      const response = await fetch(REQUEST_CODE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (response.status == 201) {
        setShowCodePrompt(true);
      }
    } else {
      console.log("Bad phone number")
    }
  }

  const handleCodeSubmit = async (e) => {
    e.preventDefault();
    if (code.length == 4) {
      let data = { physical_phone_number: "+1" + phoneNumber, code }
      const response = await fetch(SIGNUP_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (response.status == 201) {
        let noiceNumber = await response.text()
        console.log(noiceNumber)
        setNoiceNumber(noiceNumber)
      }
    }
  }

  const isPhoneNumberValid = (input) => {
    const regex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
    if (regex.test(input)) {
      return true;
    }
    else {
      alert("Invalid phone number");
      return false;
    }
  }

  const updatePhone = (e) => {
    setPhoneNumber(e.target.value)
  }

  const updateCode = (e) => {
    setCode(e.target.value)
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>NOICEMAIL</title>
        <meta name="description" content="Noicemail signup" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css"></link>
      </Head>

      {!noiceNumber &&
        <main className={styles.main}>

          <div>
            <div className="has-text-centered">
              <h1 className="title has-text-noice is-size-1 has-text-weight-bold">
                NOICEMAIL
              </h1>
              <p className="subtitle has-text-noice">{TAGLINE}</p>
            </div>
            <div className="mt-5">
              <div>
                {!showCodePrompt &&
                  <form onSubmit={handlePhoneSubmit}>
                    <div>
                      <label className="has-text-noice">
                        Your phone number:
                        <input className="input" disabled={showCodePrompt} type="tel" placeholder="555 555 5555" onChange={updatePhone} />
                      </label>
                      <div className="has-text-centered">
                        <button type="submit" className="button mt-3 is-noice has-text-white is-fullwidth">Submit</button>
                      </div>
                    </div>
                  </form>
                }
                {showCodePrompt &&
                  <form onSubmit={handleCodeSubmit}>
                    <div>
                      <div>
                        <label className="has-text-noice">
                          Verification Code:
                          <input className="input" type="text" maxLength="4" onChange={updateCode} />
                        </label>
                      </div>
                      <div className="has-text-centered">
                        <button type="submit" className="button mt-3 is-noice has-text-white is-fullwidth">Submit</button>
                      </div>
                    </div>
                  </form>
                }
              </div>
            </div>
          </div>
        </main>
      }
      {noiceNumber &&
        <div className="container has-text-centered mt-5">
          <h1>Your NoiceNumber is {noiceNumber}</h1>
          <hr />
          <p>How would you like to analyze your voicemails?</p>
          <div className="has-text-centered">
            <div className="">
              {options.map((option, i) => <button key={i} className="button m-3">{option.display_name}</button>)}
            </div>
            <div className="">
              <button type="submit" className="button mt-3 is-noice has-text-white">Submit</button>
            </div>
          </div>
        </div>
      }
    </div>
  )
}
