import Head from 'next/head'
import styles from '../styles/Home.module.css'
import { useState } from 'react'

const REQUEST_CODE_URL = "https://noicemail.deepgram.com/codes"
const SIGNUP_URL = "https://noicemail.deepgram.com/users"
const SETTINGS_URL = "https://noicemail.deepgram.com/users/<noice_number>/settings"

const TAGLINE = "It should've been a text anyways"

export default function Home() {
  const [code, setCode] = useState("")
  const [phoneNumber, setPhoneNumber] = useState("")
  const [showCodePrompt, setShowCodePrompt] = useState(false)
  const [noiceNumber, setNoiceNumber] = useState("(310) 341-7982")
  const [features, setFeatures] = useState({
    analyze_sentiment: true,
    detect_topics: true,
    detect_language: true,
    detect_entities: true,
    summarize: true,
    transcribe: true,
    translate: true,
  })

  /**
   * Handler to submit a user's phone number and receive a verification code.
   */
  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (isPhoneNumberValid(phoneNumber)) {
      let data = { physical_phone_number: formatPhoneNumber(phoneNumber) }
      const response = await fetch(REQUEST_CODE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (response.status == 201) {
        setShowCodePrompt(true);
      } else {
        alert("Something went wrong!")
      }
    } else {
      console.log("Bad phone number")
    }
  }

  /**
   * Handler to submit the verifcation code and receive a noice number. 
   */
  const handleCodeSubmit = async (e) => {
    e.preventDefault();
    if (code.length == 4) {
      let data = { physical_phone_number: formatPhoneNumber(phoneNumber), code }
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
      } else {
        alert("Something went wrong!")
      }
    }
  }

  /**
   * Handler to submit a user's ASR features.
   */
  const handleFeatureSubmit = async (e) => {
    e.preventDefault();
    const url = SETTINGS_URL.replace("<noice_number>", formatPhoneNumber(noiceNumber))
    console.log(url)
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(features),
    });
    if (response.status != 200) {
      alert("Something went wrong!")
    }
  }

  /**
   * Prepends the "+1" country code to a phone number and removes any non digits.
   */
  const formatPhoneNumber = (phoneNumber) => "+1" + phoneNumber.replace(/\D/g, '');

  /**
   * Regex to check if a phone numer is formed xxx-xxx-xxxx
   */
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

  const updateSettings = (key) => {
    let current = features[key];

    setFeatures({ ...features, [key]: !current, })
  }

  const updatePhone = (e) => {
    setPhoneNumber(e.target.value)
  }

  const updateCode = (e) => {
    setCode(e.target.value)
  }

  // Setup the feature buttons
  let featureBtns = [];
  for (const [key, value] of Object.entries(features)) {
    let btnStyle = "button is-fullwidth my-2 is-medium";
    btnStyle = value ? btnStyle + " is-noice-border" : btnStyle + " is-white";
    const btn = <button key={key} className={btnStyle} onClick={() => updateSettings(key)}>{key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ')}</button>;
    featureBtns.push(btn)
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>NOICEMAIL</title>
        <meta name="description" content="Noicemail signup" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
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
          <h1 className="has-text-weight-bold">Your NoiceNumber is {noiceNumber}</h1>
          <hr />
          <p>How would you like to analyze your voicemails?</p>
          <div className="has-text-centered">
            <div className="container">
              {featureBtns}
            </div>
            <div className="">
              <form onSubmit={handleFeatureSubmit}>
                <button type="submit" className="button mt-5 is-noice has-text-white is-medium">Submit</button>
              </form>
            </div>
          </div>
        </div>
      }
    </div>
  )
}
