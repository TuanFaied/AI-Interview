class RecorderProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0];
    if (input.length > 0) {
      const inputChannel = input[0];
      const pcm16 = new Int16Array(inputChannel.length);
      
      for (let i = 0; i < inputChannel.length; i++) {
        // Convert float32 to int16
        pcm16[i] = Math.max(-32768, Math.min(32767, inputChannel[i] * 32768));
      }
      
      this.port.postMessage(pcm16);
    }
    return true;
  }
}

registerProcessor('recorder-processor', RecorderProcessor);