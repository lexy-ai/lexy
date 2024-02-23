import "@fontsource/inter";
import { type AppType } from "next/dist/shared/lib/utils";
import Navbar from "~/components/Navbar";
import "~/styles/globals.css";

const MyApp: AppType = ({ Component, pageProps }) => {
  return (
  <>
    <Navbar />
    <Component {...pageProps} />
  </>
  );
};

export default MyApp;
