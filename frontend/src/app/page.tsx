"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function HomePage() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-80"
        style={{
          backgroundImage: "url('/asset/bg.png')"
        }}
      ></div>
      
      {/* Dark overlay for better text readability */}
      <div className="absolute inset-0 bg-black/40"></div>
      {/* Geometric Background Pattern */}
      <div className="absolute inset-0">
        {/* Concentric circles */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className="w-96 h-96 border border-red-500/10 rounded-full animate-pulse"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 border border-red-500/15 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }}></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 border border-red-500/20 rounded-full animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-red-500/25 rounded-full animate-pulse" style={{ animationDelay: '1.5s' }}></div>
        </div>
        
        {/* Larger outer circles */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className="w-[600px] h-[600px] border border-red-500/5 rounded-full animate-pulse" style={{ animationDelay: '2s' }}></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-red-500/3 rounded-full animate-pulse" style={{ animationDelay: '2.5s' }}></div>
        </div>

        {/* Diagonal lines */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-full h-full">
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1px] bg-gradient-to-r from-transparent via-red-500/10 to-transparent rotate-45"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1px] bg-gradient-to-r from-transparent via-red-500/10 to-transparent -rotate-45"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[1px] bg-gradient-to-r from-transparent via-red-500/8 to-transparent rotate-12"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[800px] h-[1px] bg-gradient-to-r from-transparent via-red-500/8 to-transparent -rotate-12"></div>
          </div>
        </div>

        {/* Floating geometric shapes */}
        <div className="absolute top-20 left-20 w-4 h-4 bg-blue-500 rounded-sm animate-bounce" style={{ animationDelay: '0s', animationDuration: '4s' }}></div>
        <div className="absolute top-32 right-32 w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '1s', animationDuration: '3s' }}></div>
        <div className="absolute bottom-40 left-40 w-2 h-2 bg-cyan-400 rotate-45 animate-bounce" style={{ animationDelay: '2s', animationDuration: '5s' }}></div>
        <div className="absolute bottom-20 right-20 w-3 h-3 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.5s', animationDuration: '3.5s' }}></div>
        <div className="absolute top-1/4 right-1/4 w-2 h-8 bg-green-500 animate-pulse" style={{ animationDelay: '1.5s' }}></div>
        <div className="absolute bottom-1/3 left-1/3 w-4 h-4 border-2 border-yellow-400 rotate-45 animate-pulse" style={{ animationDelay: '2.5s' }}></div>
        
        {/* Red dot indicator */}
        <div className="absolute top-16 right-16 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
      </div>

      {/* Mouse follower glow */}
      <div 
        className="absolute w-96 h-96 bg-gradient-radial from-blue-500/10 via-purple-500/5 to-transparent rounded-full pointer-events-none transition-all duration-300 ease-out"
        style={{
          left: mousePosition.x - 192,
          top: mousePosition.y - 192,
        }}
      ></div>

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6">
        {/* Award Badge */}
        <div className="mb-8 animate-fade-in">
          <div className="bg-gray-800/80 backdrop-blur-sm border border-gray-700 rounded-full px-6 py-3 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">∞</span>
            </div>
            <span className="text-gray-300 font-medium">Meta Impact Innovation Award</span>
            <span className="text-yellow-400 text-xl">🏆</span>
          </div>
        </div>

        {/* Main Title */}
        <div className="text-center mb-8">
          <h1 className="text-6xl md:text-8xl font-black mb-6 leading-tight">
            <span className="bg-gradient-to-r from-pink-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent animate-gradient-x">
              Security
            </span>
            <span className="text-white"> for </span>
            <span className="bg-gradient-to-r from-blue-400 via-cyan-500 to-purple-600 bg-clip-text text-transparent animate-gradient-x">
              Enterprise AI
            </span>
          </h1>
        </div>

        {/* Subtitle */}
        <div className="text-center mb-12 max-w-4xl">
          <p className="text-xl md:text-2xl text-gray-300 font-medium">
            Our suite of products - <span className="text-red-400 font-bold">Red</span> & <span className="text-blue-400 font-bold">Guard</span> secures AI Applications
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-6 mb-16">
          <Link href="/dashboard">
            <button className="group relative px-8 py-4 bg-white text-black font-bold text-lg rounded-full hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl">
              <span className="relative z-10">Explore Dashboard</span>
              <div className="absolute inset-0 bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 rounded-full opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
            </button>
          </Link>
          
          <button className="group relative px-8 py-4 border-2 border-gray-600 text-white font-bold text-lg rounded-full hover:border-white transition-all duration-300 transform hover:scale-105 backdrop-blur-sm">
            <span className="relative z-10">Contact Us</span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
          <div className="group bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 hover:border-red-500/50 transition-all duration-500 transform hover:scale-105">
            <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-600 rounded-xl flex items-center justify-center mb-4 group-hover:rotate-12 transition-transform duration-300">
              <span className="text-white font-bold text-xl">🛡️</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Red Team Testing</h3>
            <p className="text-gray-400 leading-relaxed">Advanced jailbreak detection and vulnerability assessment for AI models</p>
          </div>
          
          <div className="group bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 hover:border-blue-500/50 transition-all duration-500 transform hover:scale-105">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center mb-4 group-hover:rotate-12 transition-transform duration-300">
              <span className="text-white font-bold text-xl">🔒</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Guard Protection</h3>
            <p className="text-gray-400 leading-relaxed">Real-time AI safety monitoring and automated threat mitigation</p>
          </div>
          
          <div className="group bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 hover:border-purple-500/50 transition-all duration-500 transform hover:scale-105">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center mb-4 group-hover:rotate-12 transition-transform duration-300">
              <span className="text-white font-bold text-xl">📊</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Analytics Suite</h3>
            <p className="text-gray-400 leading-relaxed">Comprehensive security analytics and compliance reporting</p>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
        <div className="animate-bounce">
          <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>

      <style jsx>{`
        @keyframes gradient-x {
          0%, 100% {
            background-size: 200% 200%;
            background-position: left center;
          }
          50% {
            background-size: 200% 200%;
            background-position: right center;
          }
        }
        
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-gradient-x {
          animation: gradient-x 3s ease infinite;
        }
        
        .animate-fade-in {
          animation: fade-in 1s ease-out;
        }
      `}</style>
    </div>
  );
}