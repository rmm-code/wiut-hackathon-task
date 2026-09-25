export async function openVideo(
  file: File,
): Promise<{ url: string; duration: number }> {
  if (!/\.mp4$/i.test(file.name))
    throw new Error("Please choose an MP4 video.");
  if (file.size > 250 * 1024 * 1024)
    throw new Error("This video exceeds the 250 MB limit.");
  if (!file.size)
    throw new Error("This file is empty. Please choose another video.");
  const url = URL.createObjectURL(file);
  try {
    const duration = await new Promise<number>((resolve, reject) => {
      const element = document.createElement("video");
      let finished = false;
      const finish = (error?: string) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        const value = element.duration;
        element.onloadedmetadata = null;
        element.onerror = null;
        element.removeAttribute("src");
        element.load();
        error ? reject(new Error(error)) : resolve(value);
      };
      const timer = setTimeout(
        () => finish("This video could not be opened. Try an H.264 MP4."),
        10000,
      );
      element.preload = "metadata";
      element.onloadedmetadata = () => finish();
      element.onerror = () =>
        finish("This video could not be decoded. Try an H.264 MP4.");
      element.src = url;
    });
    if (!Number.isFinite(duration) || duration <= 0)
      throw new Error("This video has an invalid duration.");
    if (duration > 120.1)
      throw new Error("Choose a clip no longer than 2 minutes.");
    return { url, duration };
  } catch (error) {
    URL.revokeObjectURL(url);
    throw error;
  }
}
