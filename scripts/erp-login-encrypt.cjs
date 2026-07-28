const crypto = require('crypto')

const publicKeyBody = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCC0hrRIjb3noDWNtbDpANbjt5Iwu2NFeDwU16Ec87ToqeoIm2KI+cOs81JP9aTDk/jkAlU97mN8wZkEMDr5utAZtMVht7GLX33Wx9XjqxUsDfsGkqNL8dXJklWDu9Zh80Ui2Ug+340d5dZtKtd+nv09QZqGjdnSp9PTfFDBY133QIDAQAB'
const publicKey = `-----BEGIN PUBLIC KEY-----\n${publicKeyBody.match(/.{1,64}/g).join('\n')}\n-----END PUBLIC KEY-----`
const value = process.argv[2] || ''
const encrypted = crypto.publicEncrypt({ key: publicKey, padding: crypto.constants.RSA_PKCS1_PADDING }, Buffer.from(value))

process.stdout.write(encrypted.toString('base64'))
